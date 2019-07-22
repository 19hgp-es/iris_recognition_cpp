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
    
    //inner_circle = {0, 0, 0};
    inner_circle[0] = cvRound(circles[0][0]);
    inner_circle[1] = cvRound(circles[0][1]);
    inner_circle[2] = cvRound(circles[0][2]);

    Point center = Point(inner_circle[0], inner_circle[1]);
    circle(img, center, inner_circle[2], Scalar(0, 0, 0), FILLED);
    HoughCircles(adjusted, circles, HOUGH_GRADIENT, 1, 20, 
            canny_param, 
            hough_param, 
            inner_circle[2]+20,
            140);
                             
    /*    
    try{
        for(float circle : circles[0][0]) {
            outer_circle = {round(circles[0][0]), round(circles[0][1]), round(circles[0][2])};
            if ((abs(outer_circle[0][0] - inner_circle[0][0]) < 15) and (abs(outer_circle[0][1] - inner_circle[0][1]) < 15))
                break;
        }
    }
    */  
    outer_circle[2] = int(inner_circle[2] * 2.4);

    
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

    Mat m = Mat::zeros(Size(frame.cols, frame.rows), CV_8U);
    Point p = Point(iris_circle[0], iris_circle[1]);
    circle(m, p, iris_circle[2], Scalar(255, 255, 255), FILLED);

    bitwise_not(m, mask);
    iris_frame = frame.clone();
    subtract(frame, frame, iris_frame, mask);

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

int main(int argc, char ** argv){
    Mat image, circle, iris, norm_frame;
	FILE *fp = fopen("imagePath.txt", "r");
	
	while( !feof(fp) ){
		char strtmp[1024];
		char *pStr;
		
		pStr = fgets( strtmp, sizeof(strtmp), fp );
		strtmp[strlen(strtmp) - 1] = '\0';
		printf("%s\n", strtmp);
		
		image = imread(strtmp, 1);

		circle = detect_circles(image, 20, 20);
		iris = detect_iris_frame(circle);
		norm_frame = getPolar2CartImg(iris, iris_circle[2]);
   
		//imshow("Detect Circle", circle);
		//imshow("detect_iris_frame", iris);
		imshow("norm_frame", norm_frame);
		waitKey(1000);
		destroyWindow("norm_frame");
		
		char *filename = strrchr(strtmp, '/');
		char writePath[1024] = "/root/opencv/images/normalizedIris";
		strcat(writePath, filename);
		printf("%s\n", writePath);
		imwrite(writePath,norm_frame);
	}
	fclose(fp);
    return 0;
}
