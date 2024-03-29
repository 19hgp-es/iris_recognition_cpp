#include <opencv2/opencv.hpp>
#include <stdio.h>
#include <sys/types.h>
#include <dirent.h>
#include <string.h>
#include <unistd.h>
#include <list>

using namespace cv;
using namespace std;

list<string> imgPath;

int iris_circle[3] = {0, 0, 0};

static void on_trackbar(int, void*){

}

Mat bottom_hat_median_blurr(Mat image) {
    Mat cimg, kernel, blackhat, bottom_hat_filtered, imgRes;

    cimg = image;

    kernel = getStructuringElement(MORPH_ELLIPSE, Size(5, 5));
    morphologyEx(cimg, blackhat, MORPH_BLACKHAT, kernel);
    add(blackhat, cimg, bottom_hat_filtered);
    medianBlur(bottom_hat_filtered, imgRes, 17);
                                
    return imgRes;
}

Mat adjust_gamma(Mat image, float gamma = 1.0) {
    float inv_gamma; Mat imgRes; vector<int> table(256);

    inv_gamma = 1.0 / gamma;

    for(int i = 0 ; i < 256 ; i++) 
        table[i] = (int(pow((float(i)/255), inv_gamma) * 255));
    
    LUT(image, table, imgRes);

    return imgRes;
}

Mat detect_circles(Mat& img, int canny_param = 20, int hough_param = 20) {
    Mat filtered, adjusted;
    vector<Vec3f> circles;
    int inner_circle[3], outer_circle[3];

    filtered = bottom_hat_median_blurr(img);
    adjusted = adjust_gamma(filtered, 10);
   
    adjusted.convertTo(adjusted, CV_8U);
    cvtColor(adjusted, adjusted, COLOR_BGR2GRAY);
    HoughCircles(adjusted, circles, HOUGH_GRADIENT, 1, 20, 
            canny_param, 
            hough_param, 
            20, 
            100);
    

    inner_circle[0] = 0;
    inner_circle[1] = 0;
    inner_circle[2] = 0;

    if (circles.size() != 0){
        inner_circle[0] = cvRound(circles[0][0]);
        inner_circle[1] = cvRound(circles[0][1]);
        inner_circle[2] = cvRound(circles[0][2]);
    }

    Point center = Point(inner_circle[0], inner_circle[1]);

    circle(img, center, inner_circle[2], Scalar(0, 0, 0), FILLED);
    

    circles.clear();

    HoughCircles(adjusted, circles, HOUGH_GRADIENT, 1, 20, 
            canny_param, 
            hough_param, 
            inner_circle[2]+20,
            140);
                             
    
    if (circles.size () != 0){
        for(auto circle : circles){
            outer_circle[0] = cvRound(circle[0]);
            outer_circle[1] = cvRound(circle[1]);
            outer_circle[2] = cvRound(circle[2]);
            if(abs(outer_circle[0] - inner_circle[0]) < 15
                and abs(outer_circle[1] - inner_circle[1]) < 15){
                break;
            }
        }
    } 
    else{
        outer_circle[2] = int(inner_circle[2] * 2.4);
    }

    // for(auto circle : circles[0][0]) {
    //     outer_circle = {round(circles[0][0]), round(circles[0][1]), round(circles[0][2])};
    //     if ((abs(outer_circle[0][0] - inner_circle[0][0]) < 15) and (abs(outer_circle[0][1] - inner_circle[0][1]) < 15))
    //         break;
    // }

      
    // outer_circle[2] = int(inner_circle[2] * 2.4);

    
    outer_circle[0] = inner_circle[0];
    outer_circle[1] = inner_circle[1];


    iris_circle[0] = outer_circle[0];
    iris_circle[1] = outer_circle[1];
    iris_circle[2] = outer_circle[2];

    return img;
}

Mat detect_iris_frame(Mat frame) {
    Mat iris_frame, mask;

    if (iris_circle[0] < iris_circle[2])
        iris_circle[2] = iris_circle[0];
    if (iris_circle[1] < iris_circle[2])
        iris_circle[2] = iris_circle[1];
    if (frame.rows - iris_circle[1] < iris_circle[2])
        iris_circle[2] = frame.rows - iris_circle[1];
    if (frame.cols - iris_circle[0] < iris_circle[2])
    	iris_circle[2] = frame.cols - iris_circle[0];

    // cout << "[" << iris_circle[0] << ", " << iris_circle[1] << ", " << iris_circle[2] << "]\n";
    


    Mat m = Mat::zeros(Size(frame.cols, frame.rows), CV_8U);
    Point p = Point(iris_circle[0], iris_circle[1]);
    circle(m, p, iris_circle[2], Scalar(255, 255, 255), FILLED);

    bitwise_not(m, mask);
    iris_frame = frame.clone();
    subtract(frame, frame, iris_frame, mask, -1);


   

    
    iris_frame = iris_frame(
    	Range((iris_circle[1] - iris_circle[2]), 
            (iris_circle[1] + iris_circle[2])),
    	Range((iris_circle[0] - iris_circle[2]), 
            (iris_circle[0] + iris_circle[2])));

    return iris_frame;
}

Mat getPolar2CartImg(Mat image, int rad) {
    Mat imgRes;

    Point2f c(float(image.cols)/2.0, float(image.rows)/2.0);                         
    warpPolar(image, imgRes, Size(rad*3, 360), c, (image.cols/2)
            , WARP_POLAR_LOG);
    
    cvtColor(imgRes, imgRes, COLOR_BGR2GRAY);
    
    for(int v = rad*3-1 ; v >= 0 ; v--){
        int black_cnt = 0;
        for(int h = 0 ; h < 360 ; h++){
            if(imgRes.at<uchar>(h, v) != 0){
                black_cnt++;
            }
        }
        if(black_cnt == 0) {
            imgRes = imgRes(Range(0, 360), Range(v, rad*3));
            break;
        }
    }

    resize(imgRes, imgRes, Size(80, 360), 0, 0, INTER_CUBIC);

    return imgRes;
}

void listdir(const char *name, int indent)
{
	DIR *dir;
	struct dirent *entry;
			    
	if (!(dir = opendir(name)))
		return;
    while ((entry = readdir(dir)) != NULL) {
		if (entry->d_type == DT_DIR) {           
			char path[1024] = "";          
			if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)	
				continue;								            
			snprintf(path, sizeof(path), "%s/%s", name, entry->d_name);
			//printf("%*s[%s]\n", indent, "", entry->d_name);				            
			listdir(path, indent + 2);
		} else {
			char totalPath[1024] = "";
			snprintf(totalPath, sizeof(totalPath), "%s/%s\n", name, entry->d_name);
			imgPath.push_back(totalPath);
		}
	}
	closedir(dir);
}

Mat makegray(Mat &src){
    Mat ret = src.clone();
    int sum = 0;
    cout << "cols : " << ret.cols << " rows : " << ret.rows;
    for(int i = 0 ; i < ret.rows ; i++){
        for(int j = 0 ; j < ret.cols ; j++){
            if(ret.at<uchar>(i, j) >= 127)
                ret.at<uchar>(i, j) = 127;
        }
    }
    return ret;
}

void draw_new_circles(Mat &src, Mat &dst, int p1, int p2){
    Mat temp;
    dst = src.clone();
    vector<Vec3f> circles;
    vector<Point> p;
    vector<int> rad;
    int new_circle[3] = {0, 0, 0};

    Canny(src, temp, p1, p2);
    HoughCircles(temp, circles, HOUGH_GRADIENT, 1, 40, 20, 10, 100);
    
    if(circles.size() != 0){
        int cnt = 0;
        for(auto circle : circles){
            new_circle[0] = cvRound(circle[0]);
            new_circle[1] = cvRound(circle[1]);
            new_circle[2] = cvRound(circle[2]);

            // cout << new_circle[0] << " " << new_circle[1] << " " << new_circle[2] << endl;
            Point center = Point(new_circle[0], new_circle[1]);
            p.push_back(center);
            rad.push_back(new_circle[2]);
        }
        for(int i = 0 ; i < circles.size() ; i++){
            // if(p[i].x >= src.cols and p[i].y - rad[i] > 0 and p[i].y + rad[i] < src.rows){
                circle(dst, p[i], rad[i], Scalar(0, 0, 255), 2);
                // cnt++;
            // }
        }
        cout << "circles.size() : " << cnt << endl;
    }
    else{
        cout << "no circle detected!\n";
    }
}

int main(int argc, char ** argv){
    Mat image, temp_image, d_circle, iris, norm_frame, norm_canny, temp_norm_frame;
    Mat test;
	FILE *fp = fopen("imagePath.txt", "r");
	
    int cnt = 1;
	while( !feof(fp) ){
		char strtmp[1024];
		char *pStr;
		
		pStr = fgets( strtmp, sizeof(strtmp), fp );
		strtmp[strlen(strtmp)-1] = '\0';
		printf("%s\n", strtmp);
		
		image = imread(strtmp, 1);
        temp_image = image.clone(); 
		d_circle = detect_circles(temp_image);
		iris = detect_iris_frame(d_circle);
		norm_frame = getPolar2CartImg(iris, iris_circle[2]);

        imshow("norm_frame", norm_frame);
        
        // draw_new_circles(norm_frame, test, 10, 200);
        // imshow("find circle?", test);
        // test = makegray(norm_frame);
        // imshow("norm_frame", test);

        waitKey(100000);
        // namedWindow("Canny");

        // createTrackbar("low threshold", "Canny", 0, 1000, on_trackbar);
        // createTrackbar("high threshold", "Canny", 0, 1000, on_trackbar);

        // setTrackbarPos("low threshold", "Canny", 50);
        // setTrackbarPos("high threshold", "Canny", 150);



        // while(1){
        //     temp_norm_frame = norm_frame.clone();
        //     int low = getTrackbarPos("low threshold", "Canny");
        //     int high = getTrackbarPos("high threshold", "Canny");

        //     Canny(norm_frame, norm_canny, low, high);

        //     vector<Vec3f> circles;
        //     vector<Point> p;
        //     vector<int> rad;

        //     HoughCircles(norm_canny, circles, HOUGH_GRADIENT, 1, 20, 20, 20, 140);


        //     int new_circle[3] = {0, 0, 0};
        //     if(circles.size() != 0){
        //         cout << "circles.size() : " << circles.size() << endl;
        //         for(auto circle : circles){
        //             new_circle[0] = cvRound(circle[0]);
        //             new_circle[1] = cvRound(circle[1]);
        //             new_circle[2] = cvRound(circle[2]);

        //             cout << new_circle[0] << " " << new_circle[1] << " " << new_circle[2] << endl;
        //             Point center = Point(new_circle[0], new_circle[1]);
        //             p.push_back(center);
        //             rad.push_back(new_circle[2]);
        //         }
        //         for(int i = 0 ; i < circles.size() ; i++){
        //             circle(temp_norm_frame, p[i], rad[i], Scalar(0, 0, 255), 2);
        //         }

        //     }
        //     else{
        //         cout << "no circle detected!\n";
        //     }
        //     cout << "low : " << low << "\n";
        //     cout << "high : " << high << "\n";
        //     imshow("temp_norm_frame", temp_norm_frame);
        //     imshow("norm_frame", norm_frame);
        //     imshow("Canny", norm_canny);
        //     moveWindow("temp_norm_frame", 0, 0);
        //     moveWindow("norm_frame", 150, 0);
        //     moveWindow("Canny", 300, 0);

        //     if(waitKey(1) == 27)
        //         break;
        // }
	}
	fclose(fp);
    return 0;
}
