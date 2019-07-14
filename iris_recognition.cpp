#include <opencv2/opencv.hpp>
#include <cmath>
#include <vector>
#include <algorithm>

using namespace cv;
using namespace std;

vector<Vec3f> iris_circle = {0, 0, 0};

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
    float inv_gamma; Mat imgRes; vector<int> table;

    inv_gamma = 1.0 / gamma;

    for(int i = 0 ; i < 256 ; i++) 
        table.push_back(int(pow((float(i)/255), inv_gamma) * 255));

    LUT(image, table, imgRes);

    return imgRes;
}

void detect_circles(Mat img, int canny_param = 20, int hough_param = 20) {
    Mat filtered, adjusted;
    vector<Vec3f> circles, outer_circle, circle_frame;
    vector<Vec3i> inner_circle;

    filtered = bottom_hat_median_blurr(img);
    adjusted = adjust_gamma(filtered, 10);
    HoughCircles(adjusted, circles, HOUGH_GRADIENT, 1, 20, 
            canny_param, 
            hough_param, 
            20, 
            100);

    inner_circle = {0, 0, 0};
    if(circles != NULL)  
        inner_circle.push_back(round(circles[0][0]));
    circle_frame = circle(img, Point(inner_circle[0], inner_circle[1]), 
            inner_circle[2], Scalar(0, 0, 0), FILLED);

    HoughCircles(adjusted, circles, CV_HOUGH_GRADIENT, 1, 20, 
            canny_param, 
            hough_param, 
            inner_circle[2]+20,
            140);
                                           
    outer_circle = {0, 0, 0};
    if(circles != NULL){
        for(float circle : circles[0]) {
            outer_circle.push_back(round(circles));
            if ((abs(outer_circle[0] - inner_circle[0]) < 15) and (abs(outer_circle[1] - inner_circle[1]) < 15))
                break;
        }
    }
    else
        outer_circle[2] = int(inner_circle[2] * 2.4);
    outer_circle[0] = inner_circle[0];
    outer_circle[1] = inner_circle[1];

    iris_circle = outer_circle;

    return circle_frame;
}

Mat detect_iris_frame(Mat frame) {
    Mat iris_frame;
    Mat imgRet;
    int a = 0, b = 0;
    if (iris_circle[0] < iris_circle[2])
        iris_circle[2] = iris_circle[0];
    if (iris_circle[1] < iris_circle[2])
        iris_circle[2] = iris_circle[1];
    if (frame.shape[0] - iris_circle[1] < iris_circle[2])
        iris_circle[2] = frame.shape[0] - iris_circle[1];
    if (frame.shape[1] - iris_circle[0] < iris_circle[2])
    	iris_circle[2] = frame.shape[1] - iris_circle[0];

    /*
       mask = cv.bitwise_not(
       cv.circle(np.zeros((np.size(frame,0),np.size(frame,1),1), np.uint8)
       , (iris_circle[0], iris_circle[1]), iris_circle[2], (255,255,255), cv.FILLED))
     */

    bitwise_not(circle())


        iris_frame = frame.clone();
    subtract(frame, frame, iris_frame, mask, -1);

    /*
       line 94 ~ 98
     */

    imgRet = iris_frame(
    	Range(iris_circle[1] - iris_circle[2], 
    		iris_circle[1] + iris_circle[2]),
    	Range(iris_circle[0] - iris_circle[2], 
    		iris_circle[0] + iris_circle[2]));

    return imgRet;
}

Mat getPolar2CartImg(Mat image, int rad) {
    Mat imgRes, Mat imgRet, int black_cnt = 0;
    int a = 0, b = 0;

    Point2f c(float(image.cols)/2, float(image.rows)/2); 
    warpPolar(image, imgRes, Size(rad*3, 360), c, (image.rows/2), CV_WARP_POLAR_LOG);
                            
    for(int v = rad*3-1 ; v >= 0 ; i--){
        black_cnt = 0;
        for(int h = 0 ; h < 360 ; ++h){
            if(imgRes.at<int>(h,v) != 0){
                black_cnt++;
            }
        }
        if(black_cnt == 0) {
            imgRet = imgRes(Range(0, 360), Range(v, rad*3));
            break;
        }
    }

    resize(imgRet, imgRet, Size(80, 360), 0, 0, CV_INTER_CUBIC);

    return imgRet;
}
