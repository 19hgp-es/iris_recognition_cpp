import cv2 as cv
import math
import numpy as np
import os
import time
#input_img_path = "C:\\Users\\ANTICODE\\Documents\\Iris\\iris_data\\MMUIrisDatabase\\MMU_Iris_Database"
#output_path = "C:\\Users\\ANTICODE\\Documents\\Iris\\iris_recognition\\images\\MMUIris_norm"
# input_img_path = "/home/metaljsw2/iris_processing/CASIA-IrisV4(JPG)/CASIA-Iris-Interval"
# output_path = "/home/metaljsw2/CASIA_Iris_interval_norm"

filepath1 = "CASIA-IrisV4(JPG)/"
filepath2 = "CASIA-Iris-Lamp"

# filepath1 = ""
# filepath2 = "MMU_Iris_Database"

input_img_path = "/Users/leejonguk/Desktop/hanyang/project/iris/"+filepath1+filepath2
output_path = "/Users/leejonguk/Desktop/norm_imgs/"+filepath1+filepath2

iris_circle = [0, 0, 0]

inner_temp = [0, 0, 0]


inner_circle_rad_list = list()
outer_circle_rad_list = list()

inner_circle_rad_dict = dict()
outer_circle_rad_dict = dict()

file_name_list = list()


def bottom_hat_median_blurr(image):

    cimg = image
    
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (5, 5))
    blackhat = cv.morphologyEx(cimg, cv.MORPH_BLACKHAT, kernel)
    bottom_hat_filtered = cv.add(blackhat, cimg)
    
    return cv.medianBlur(bottom_hat_filtered, 17)

def adjust_gamma(image, gamma=1.0):
  
    inv_gamma = 1.0 / gamma
    table = np.array(
    	[ ((i / 255.0) ** inv_gamma) * 255
	for i in np.arange(0, 256)]).astype("uint8")
    return cv.LUT(image, table)




























def detect_circles(img, canny_param=20, hough_param=20):
    global inner_circle_rad_list, outer_circle_rad_list, inner_temp

    filtered = bottom_hat_median_blurr(img)
    adjusted = adjust_gamma(filtered, 10)
    #case mmu => min_rad = 15, max_rad = 40

    if(filepath2 == "MMU_Iris_Database" ):
	    #mmu min 15 max 40
	    circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
	    							param1=canny_param,
	    							param2=hough_param,
	    							minRadius=15,
	    							maxRadius = 40)

    elif filepath2 == "CASIA-Iris-Lamp":
	    circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
	    							param1=canny_param,
	    							param2=hough_param,
	    							minRadius=15,
	    							maxRadius = 60)
    
    elif filepath2 == "CASIA-Iris-Thousand":
	    circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
	    							param1=canny_param,
	    							param2=hough_param,
	    							minRadius=20,
	    							maxRadius = 60)
    
    elif filepath2 == "CASIA-Iris-Syn":
	    circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
	    							param1=canny_param,
	    							param2=hough_param,
	    							minRadius=20,
	    							maxRadius = 60)
    
    else:
        circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
	    							param1=canny_param,
	    							param2=hough_param,
	    							minRadius=20,
	    							maxRadius=100)

    inner_circle = [0, 0, 0]
    if circles is not None:
    	inner_circle = np.uint16(np.around(circles[0][0])).tolist()

    circle_frame = cv.circle(img, (inner_circle[0], inner_circle[1]), 
    					inner_circle[2], (0,0,0), cv.FILLED)
    
    # print("내부 반지름 : " + str(inner_circle[2]))
    inner_circle_rad_list.append(inner_circle[2])

    print(inner_circle[2])
    inner_temp = inner_circle

    if inner_circle[2] in inner_circle_rad_dict:
    	inner_circle_rad_dict[inner_circle[2]] += 1
    else:
    	inner_circle_rad_dict[inner_circle[2]] = 1
    #case mmu => min_rad = inner_circle[2]+20, max_rad = 60

    if filepath2 == "MMU_Iris_Database":
	    circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
									param1=canny_param,
									param2=hough_param,
									minRadius=inner_circle[2]+20,
									maxRadius=60)

    elif filepath2 == "CASIA-Iris-Lamp":
	    circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
									param1=canny_param,
									param2=hough_param,
									minRadius=inner_circle[2]+20,
									maxRadius=100)
    
    elif filepath2 == "CASIA-Iris-Thousand":
    	circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
									param1=canny_param,
									param2=hough_param,
									minRadius=inner_circle[2]+20,
									maxRadius=100)

    else:
        circles = cv.HoughCircles(adjusted, cv.HOUGH_GRADIENT, 1, 20,
									param1=canny_param,
									param2=hough_param,
									minRadius=inner_circle[2]+20,
									maxRadius=140)






    outer_circle = [0, 0, 0]
    if circles is not None:
    	print("outer_circle detected.")

    	for circle in circles[0]:
    		outer_circle = np.uint16(np.around(circle)).tolist()
			
    		if (abs(outer_circle[0] - inner_circle[0]) < 15) and (abs(outer_circle[1] - inner_circle[1]) < 15):
		    	outer_circle_rad_list.append(outer_circle[2])
		    	if outer_circle[2] in outer_circle_rad_dict:
		    		outer_circle_rad_dict[outer_circle[2]] += 1
		    	else:
		    		outer_circle_rad_dict[outer_circle[2]] = 1
    			break
    else:
    	#case mmu =>  int(inner_circle[2] * 2.4)
    	print("outer_circle not detected.")
    	# outer_circle[2] = int(inner_circle[2] * 2.4)

    	if filepath2 == "MMU_Iris_Database":
    		outer_circle[2] = 55

    	elif filepath2 == "CASIA-Iris-Lamp":
    		outer_circle[2] = 73

    	else :
    		outer_circle[2] = int(inner_circle[2] * 2.4)
    outer_circle[0], outer_circle[1] = inner_circle[0], inner_circle[1]

    if filepath2 == "MMU_Iris_Database":
    	outer_circle[2] = 56

    elif filepath2 == "CASIA-Iris-Lamp":
    	outer_circle[2] = 100

    elif filepath2 == "CASIA-Iris-Interval":
    	outer_circle[2] = 100

    elif filepath2 == "CASIA-Iris-Syn":
    	outer_circle[2] = 85  

    elif filepath2 == "CASIA-Iris-Thousand":
    	outer_circle[2] = 82

    global iris_circle
    iris_circle = outer_circle

    return circle_frame



































def detect_iris_frame(frame):
	
	global iris_circle
	#for casia_dabase
	if iris_circle[0] < iris_circle[2]:
		iris_circle[2] = iris_circle[0]
	if iris_circle[1] < iris_circle[2]:
		iris_circle[2] = iris_circle[1]
	if frame.shape[0] - iris_circle[1] < iris_circle[2]:
		iris_circle[2] = frame.shape[0] - iris_circle[1]
	if frame.shape[1] - iris_circle[0] < iris_circle[2]:
		iris_circle[2] = frame.shape[1] - iris_circle[0]

	mask = cv.bitwise_not(cv.circle(np.zeros((np.size(frame,0),np.size(frame,1),1), np.uint8)
					, (iris_circle[0], iris_circle[1]), iris_circle[2], (255,255,255), cv.FILLED))
	

	iris_frame = frame.copy()
	iris_frame = cv.subtract(frame, frame, iris_frame, mask, -1)
	# cv.subtract(frame, frame, iris_frame, mask, -1)

	# print(iris_circle[1])
	# print(iris_circle[2])

	iris_frame = iris_frame[(iris_circle[1] - iris_circle[2]):(iris_circle[1] + iris_circle[2]),
						(iris_circle[0] - iris_circle[2]):(iris_circle[0] + iris_circle[2])]
	# print(iris_circle)
	# print(iris_circle[1] - iris_circle[2])
	return iris_frame

	# return iris_frame[(iris_circle[1] - iris_circle[2]):(iris_circle[1] + iris_circle[2]),
	# 					(iris_circle[0] - iris_circle[2]):(iris_circle[0] + iris_circle[2])]

def getPolar2CartImg(image, rad):

	c = (float(np.size(image, 0)/2.0), float(np.size(image, 1)/2.0))
	
	imgRes = cv.warpPolar(image, (rad*3,360), c, np.size(image, 0)/2, cv.WARP_POLAR_LOG)


	for valid_width in reversed(range(rad*3)):
		blank_cnt = 0
		for h in range(360):
			if (imgRes[h][valid_width] != 0):
				blank_cnt+=1
		if(blank_cnt == 0):
			imgRes = imgRes[0:360, valid_width:rad*3]
			break

	imgRes = cv.resize(imgRes, (80, 360), interpolation=cv.INTER_CUBIC)
	

	return (imgRes)


startTime = time.time()

key = 0
print("start image processing")

err_list = ["S6510S00.jpg", 
			"S1023R05.jpg",
"S1023R04.jpg",
"S1023R03.jpg",
"S1220L02.jpg",
"S1148L03.jpg"]

error_list = list()
total_pic = 0
for (path, dir, files) in os.walk(input_img_path):
	
#	if not(os.path.isdir(output_path+ path.split("MMU_Iris_Database")[1])):
#		os.mkdir(output_path +path.split("MMU_Iris_Database")[1])
	if not(os.path.isdir(output_path+ path.split(filepath2)[1])):
		os.mkdir(output_path +path.split(filepath2)[1])
	for filename in files:
		ext = os.path.splitext(filename)[-1]
		if ((ext == '.bmp') or (ext == '.jpg')):
			total_pic += 1

			
			print(filename + "   " + str(total_pic))

			frame = cv.imread(path + "/" + filename, cv.CV_8UC1)
			temp = frame.copy()
			circle = detect_circles(frame)
		
			iris = detect_iris_frame(circle)

			try:
				norm_frame = getPolar2CartImg(iris,iris_circle[2])

			except cv.error:
				print("cv2 error detected..")
				error_list.append(filename)
				continue
			#print(frame.shape)
			cv.circle(temp, (iris_circle[0], iris_circle[1]), 
    					iris_circle[2], (255,255,255), 4)
			cv.circle(temp, (inner_temp[0], inner_temp[1]),
						inner_temp[2], (255,255,255), 4)

			cv.imshow("input", temp)
			cv.imshow("iris",circle)
			cv.imshow("iris",iris)
			cv.imshow("normalized", norm_frame)


			if (iris_circle[2] - inner_temp[2] < 10):
				cv.waitKey(100000)
				print("error1")

			if filename in err_list:
				cv.waitKey(100000)
				print("error2")

			cv.imwrite(output_path + path.split(filepath2)[1] + "/" + filename, norm_frame)

			key = cv.waitKey(1)
			if (key == 27 or key == 1048603):
				break	

	# if total_pic == 100:
	# 	break
inner_circle_rad_list.sort()
outer_circle_rad_list.sort()

print("total pictures : " + str(total_pic))
if len(inner_circle_rad_list) != 0:
	print("inner_circle_avg : " +  str(sum(inner_circle_rad_list)) + " / " + str(len(inner_circle_rad_list)) + " = " + str(sum(inner_circle_rad_list) / len(inner_circle_rad_list)))
	print("inner_circle min_val : " + str(inner_circle_rad_list[0]))
	print("inner_circle max_val : " + str(inner_circle_rad_list[-1]))
	print()

if len(outer_circle_rad_list) != 0:
	print("outer_circle_avg : " +  str(sum(outer_circle_rad_list)) + " / " + str(len(outer_circle_rad_list)) + " = " + str(sum(outer_circle_rad_list) / len(outer_circle_rad_list)))
	print("outer_circle min_val : " + str(outer_circle_rad_list[0]))
	print("outer_circle max_val : " + str(outer_circle_rad_list[-1]))
	print()

"""
print(filepath2)

print("total_pic :", total_pic)

print("error_list :")

print(len(error_list))

error_list.sort()
for item in error_list:
	print(item)


"""
endTime = time.time() - startTime

print(endTime)

inner_circle_rad_list.sort()
outer_circle_rad_list.sort()

inner_key = list(inner_circle_rad_dict.keys())
outer_key = list(outer_circle_rad_dict.keys())
inner_key.sort()
outer_key.sort()

for item in inner_key:
	print(str(item) + " : " + str(inner_circle_rad_dict[item]))

for item in outer_key:
	print(str(item) + " : " + str(outer_circle_rad_dict[item]))




with open(output_path + '/error_file.txt', 'w') as file:
	file.write("execution time : " + str(endTime) + "\n\n")
	file.write("number of pictures : " + str(total_pic) + "\n\n")
	file.write("inner_circle_avg : " +  str(sum(inner_circle_rad_list)) + " / " + str(len(inner_circle_rad_list)) + " = " + str(sum(inner_circle_rad_list) / len(inner_circle_rad_list)) + "\n")
	file.write("inner_circle min_val : " + str(inner_circle_rad_list[0]) + "\n")
	file.write("inner_circle_max_val : " + str(inner_circle_rad_list[-1]) + "\n")
	
	file.write("inner_circle_radius values\n\n")
	for item in inner_key:
		file.write(str(item) + " : " + str(inner_circle_rad_dict[item]) + "\n")

	file.write("outer_circle_radius values\n\n")
	for item in outer_key:
		file.write(str(item) + " : " + str(outer_circle_rad_dict[item]) + "\n")



	file.write("outer_circle_avg : " +  str(sum(outer_circle_rad_list)) + " / " + str(len(outer_circle_rad_list)) + " = " + str(sum(outer_circle_rad_list) / len(outer_circle_rad_list)) + "\n")
	file.write("outer_circle min_val : " + str(outer_circle_rad_list[0]) + "\n")
	file.write("outer_circle_max_val : " + str(outer_circle_rad_list[-1]) + "\n")
	
	file.write("number of Errors : " + str(len(error_list)) + "\n")      
	for item in error_list:
		file.write(item + "\n")


cv.destroyAllWindows()