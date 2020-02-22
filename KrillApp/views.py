import ast
import csv
import io
import json
import os
import cv2
import pickle
import smtplib
import threading
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import COMMASPACE

import csvsqlite3
import numpy as np
import scipy.io
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from KrillApp.forms import ImageForm, TripForm
from KrillApp.models import Image, Krill, Trip
from .forms import StatForm


def Pass_Form(request):
    if request.method == 'POST':
        # print("helooo")
        form = StatForm(request.POST)
        # print("111")
        if form.is_valid():
            # print("WORKED")
            # print(form)
            board = form.cleaned_data['board']
            event = form.cleaned_data['event']
            net = form.cleaned_data['net']
            print(board)
            print(event)
            print(net)
            return HttpResponseRedirect('/via/')
    else:
        print("NO WORK")
        form = StatForm()
    return HttpResponseRedirect('/via')


def Upload_Image(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user_name = request.user.username
            instance.user = request.user
            instance.save()
            return HttpResponseRedirect('/images_successful')
    else:
        form = ImageForm()
    return render(request, 'images_upload.html', {'form': form})


def Create_Trip(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            return HttpResponseRedirect('/view_trips')
    else:
        form = TripForm()
    return render(request, 'create_trip.html', {'form': form})


# gets and displays user images
def Get_User_Images(request):
    sql = 'SELECT * FROM Krillapp_image WHERE user_id="' + str(request.user.id) + '";'
    urls = []
    images = Image.objects.raw(sql)
    for image in images:
        urls.append(str(image.image_file).replace("user_" + str(request.user.id), ""))
    return render(request, 'images_view.html', {'images': images, 'urls': urls})

def Get_Image_Cruise_Details(request):
    sql = 'SELECT * FROM Krillapp_image WHERE file_name="' + str(request.GET["image"].split(" ")[0].split("/")[3]) + '";'
    ds = []
    details = Image.objects.raw(sql)
    for d in details:
        return JsonResponse({
            'board': str(d.board),
            'net': str(d.net),
            'event': str(d.event),
            'altr_view': str(d.altr_view),
            'position': str(d.position)
        })

def Get_User_Trips(request):
    sql = 'SELECT * FROM Krillapp_trip;'
    trip_list = []
    trips = Trip.objects.raw(sql)
    for trip in trips:
        trip_list.append(str(trip.trip_name))
    return render(request, 'view_trips.html', {'trip_list': trip_list})


# FIX DELETE
def Get_Trip_Image_List(request):
    sql = 'SELECT * FROM Krillapp_image WHERE trip_name_id="' + str(request.POST['trip_to_get']) + '";'
    trip_image_list = []
    images = Image.objects.raw(sql)
    for image in images:
        trip_image_list.append(str(image.image))
    #print(trip_image_list)
    return JsonResponse({
        'trip_image_list': trip_image_list,
    })


def Delete_Trip(request):
    Trip.objects.filter(trip_name=request.POST['trip_to_delete']).delete()
    return HttpResponseRedirect('/view_trips')


def Upload_Image_To_Trip(request):
    trips = Trip.objects.all()
    return render(request, 'upload_image_to_trip.html', {'trips': trips})


# todo fix lmao


def Delete_User_Image(request):
    print(Image.objects.filter(image=request.POST['image_url']).delete())
    return HttpResponse('/via')


def View_Trip_Image(request):
    html = render_to_string('view_trip_image.html',
                            {'image_url': request.POST['image_url'], 'raw_url': request.POST['stripped_url']},
                            request=request)
    return HttpResponse(html)


class BasicUploadView(View):
    def get(self, request):
        photos_list = Image.objects.all()
        return render(self.request, 'upload_image_to_trip.html', {'photos': photos_list})

    def post(self, request):
        form = ImageForm(self.request.POST, self.request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.trip_name = Trip.objects.get(trip_name__exact=request.POST['trip_name'])
            instance.user_name = request.user.username
            instance.user = request.user
            instance.file_name = str(instance.image)
            instance.save()
            data = {'is_valid': True, 'url': instance.file_name}
        else:
            data = {'is_valid': False}
        return JsonResponse(data)


def Load_VIA(request):
    # Process_Krill_Photo()
    sql = 'SELECT * FROM Krillapp_trip;'
    trip_list = []
    trips = Trip.objects.raw(sql)
    for trip in trips:
        trip_list.append(str(trip.trip_name))
    return render(request, 'via.html', {'trips': trips})

class AltViewAPIView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        # Saves the annotations to the image table too
        file_name = request.data['image_file']
        # image = Image.objects.get(file_name=request.data['alt_img'].split('/')[-1])
        krill_attributes = request.data['krill_attributes']
        bounding_boxes = []
        region_id = request.data['region']
        for x in list(Krill.objects.all()):
            if (x.image_file_id==request.data['image_file'].split('/')[-1]):
                bounding_boxes.append({
                    "width": x.width,"height": x.height,"x": x.x,"y": x.y
                })
        krill_attributes = ast.literal_eval(krill_attributes)
        region_id = ast.literal_eval(region_id)
        Image.objects.filter(image=file_name).update(altr_view=request.data['alt_img'])
        Image.objects.filter(image=str(request.data['alt_img'])).update(altr_view=file_name)
        # for i in range(len(bounding_boxes)):
        #     box_info = bounding_boxes[i]
        #     Krill.objects.update_or_create(
        #         unique_krill_id=request.data['alt_img'].split('/')[-1] + "-" + str(region_id[i]),
        #         defaults={
        #             'altr_width': box_info['width'],
        #             'altr_height': box_info['height'],
        #             'altr_x': box_info['x'],
        #             'altr_y': box_info['y'],
        #             'image_file': image,
        #             'altr_view': file_name.split('/')[-1]
        #         }
        #     )
        return Response("Done")
class ImageAnnotationsAPIView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        file_name = request.data['image_file'].split('/')[-1]     
        if (len(request.data['image_annotations']) < 5):
            return HttpResponseBadRequest("Here's the text of the Web page.")
        Image.objects.filter(file_name=file_name).update(image_annotations=request.data['image_annotations'])
        image = Image.objects.get(file_name=file_name)
        bounding_boxes = request.data['image_annotations']
        bounding_boxes_for_later_use = bounding_boxes
        krill_attributes = request.data['krill_attributes']
        region_id = request.data['region']
        # Removing the square brackets and quotations from the string
        bounding_boxes = bounding_boxes[2:]
        bounding_boxes = bounding_boxes[:-2]
        # Split the string into individual annotations
        bounding_boxes = bounding_boxes.split('","')
        krill_attributes = ast.literal_eval(krill_attributes)
        region_id = ast.literal_eval(region_id)
        Image.objects.filter(file_name=file_name).update(
            net=request.data['event'],
            event=request.data["net"],
            board=request.data["board"],
            position=request.data["position"]
        )
        for i in range(len(krill_attributes)):
            unique_id = str(image.file_name) + "-" + str(region_id[i])
            box_info = ast.literal_eval(bounding_boxes[i].replace("\\", ""))
            # print("_______________")
            # print(box_info['height'])
            # box_info['height'] += 500
            # box_info['width'] += 900
            # print(box_info['height'])
            # print(bounding_boxes[i])
            # print("_______________")
            obj, created = Krill.objects.update_or_create(
                unique_krill_id=unique_id,
                defaults={'x': box_info['x'],
                          'y': box_info['y'], 'width': box_info['width'], 'height': box_info['height'],
                          'bounding_box_num': str(region_id[i]), 'unique_krill_id': unique_id, 'image_file': image,
                          'image_annotation': bounding_boxes[i], 'length': krill_attributes[i]['Length'],
                          'maturity': krill_attributes[i]['Maturity'], 'position': request.data["position"], 'event': request.data["net"],
                          'net': request.data["event"], 'board': request.data["board"], 'altr_view': image.altr_view}
            )
        bb = []
        ri = request.data['region']
        ka = request.data['krill_attributes']
        # print(len(request.data['alt_img']))
        # altri = Image.objects.get(file_name=request.data['alt_img'].split('/')[-1])
        # print("_______________")
        # print(altri)
        # print("_______________")
        for x in list(Krill.objects.all()):
            if (x.image_file_id==request.data['image_file'].split('/')[-1]):
                bb.append({
                    "width": x.width,"height": x.height,"x": x.x,"y": x.y
                })
        ka = ast.literal_eval(ka)
        ri = ast.literal_eval(ri)
        if (len(request.data['alt_img']) > 5):
            img = Image.objects.get(file_name=request.data['alt_img'].split('/')[-1])
            for i in range(len(bb)):
                box_info = bb[i]
                Krill.objects.update_or_create(
                    unique_krill_id=request.data['alt_img'].split('/')[-1] + "-" + str(region_id[i]),
                    defaults={
                        'altr_width': box_info['width'],
                        'altr_height': box_info['height'],
                        'altr_x': box_info['x'],
                        'altr_y': box_info['y'],
                        'image_file': img,
                        'altr_view': img.altr_view,
                        'position': img.position
                    }
                )

        # Image.objects.filter(file_name=request.data['alt_img'].split('/')[-1]).update(image_annotations=bounding_boxes_for_later_use)
        return Response("Done")


def Load_Image_Annotations(request):
    Images = Image.objects.filter(image=request.POST['image_file'])
    firstImage = Images.first()
    krill = Krill.objects.filter(unique_krill_id__contains=str(firstImage.file_name))
    data = json.dumps(list(krill.values()), cls=DjangoJSONEncoder, ensure_ascii=False)
    # print(data)
    return JsonResponse({
        'annotations': firstImage.image_annotations,
        'region_attributes': data,

    })


def Pull_From_CSV(request):
    #Get_Image_Cruise_Details(request)
    image = Image.objects.get(image=str(request.POST['image']))
    print(str(request.POST['image']))
    if ('JR260B' in str(request.POST['image'])):
        conn = csvsqlite3.connect('JR260B.csv')
    elif ('JR255A' in str(request.POST['image'])):
        conn = csvsqlite3.connect('JR255A.csv')
    elif ('JR291_Event' in str(request.POST['image'])):
        conn = csvsqlite3.connect('JR291.csv')
    elif ('Event' in str(request.POST['image'])):
        conn = csvsqlite3.connect('JR280.csv')
    elif ('DSC' in str(request.POST['image'])):
        conn = csvsqlite3.connect('JR15002.csv')
    else:
        pass
    
        
    print(image)
    cur = conn.cursor()
    # print(cur.execute("select * from csv WHERE Lateral OR Dorsal='"+ str(image.file_name) +"'"))
    # Do it like this, trust me
    xyz = "'" + str(image.file_name) + "'"
    abc = "select * from csv WHERE Lateral = " + xyz + " or Dorsal = " + xyz
    print(abc)
    # print(abc)
    cur.execute(abc)
    # print(str(image.file_name))
    excel_data = cur.fetchall()
    # for a in excel_data:
    #     print(a)

    krill_to_update = Krill.objects.filter(unique_krill_id__contains=str(image.file_name))
    img_to_update = Image.objects.filter(file_name=str(image.file_name))
    # print(krill_to_update)
    # print("IMG TO UPDATE:")
    # print(img_to_update)
    # print(len(excel_data))
    a = Image.objects.filter(file_name=str(image.file_name)).get()
    img_list = [a] * len(excel_data)
    print(img_list)
    for i in range(len(excel_data)):
        if i < len(excel_data):
            print(excel_data[i])
            test = krill_to_update[i]
            img = img_list[i]
            img.board = excel_data[i][5]
            img.event = excel_data[i][0]
            img.net = excel_data[i][2]
            if (image.file_name == excel_data[i][6]):
                img.position = 'Dorsal'
                test.position = 'Dorsal'
            elif (image.file_name == excel_data[i][7]):
                img.position = "Lateral"
                test.position = 'Lateral'
            else:
                pass
            print('______________________')
            print(krill_to_update[i])
            print('______________________')
            print(img_list[i])
            test.length = excel_data[i][3]
            print('______________________')
            print(excel_data[i][3])
            print('______________________')
            test.maturity = excel_data[i][4]
            print(excel_data[i][4])
            print('______________________')
            test.lateral = excel_data[i][6]
            test.dorsal = excel_data[i][7]
            test.event = excel_data[i][0]
            test.net = excel_data[i][2]
            test.board = excel_data[i][5]
            test.save()
            img.save()
    conn.close()
    return JsonResponse({
        'num_pulled': len(excel_data),
    })


def Export_To_CSV(request):
    trip = str(request.POST['trip'])
    email = str(request.POST['eml'])
    thread = threading.Thread(target=Extract_And_Send_CSV, args=(trip,email))
    thread.daemon = True
    thread.start()
    return HttpResponseRedirect('/view_trips')


def Extract_Images(request):
    trip = str(request.POST['trip'])
    krill = Krill.objects.all().values('length', 'maturity', 'x', 'y', 'width',
                                                                        'height', 'image_file_id', 'lateral', 'dorsal',
                                                                        'unique_krill_id')
    krill = list(krill)
    i = 0
    for row in krill:
        if (row['maturity'] != "Unclassified"):
            print(row)
            print("Start")
            x = int(row['x'])
            y = int(row['y'])
            w = int(row['width'])
            h = int(row['height'])
            image = Image.objects.get(file_name=row['image_file_id'])
            image = cv2.imread("media/" + str(image.image))
            image = image[y:y + h, x:x + w]
            imgName = row['unique_krill_id'] + '.jpg'
            pathName = '/Users/mazgudelis/Desktop/ComputerVision/Krill images/' + imgName
            cv2.imwrite(pathName, image)
            i = i + 1
            print(str(i) + '/' + str(len(krill)))
            # add bouding box to csv a welll for LAt and DORs
            # add id 
            # doo all manual labor till end of week
            # use small arch like alexnet, vgg ,aybe bigger like reznet
            # add readme txt to csv file that says what incermented

            
    return HttpResponseRedirect('/view_trips')


def Extract_And_Send_CSV(trip, eml):
    # print(trip)
    # print(eml)
    csvfile = io.StringIO()
    writer = csv.writer(csvfile)
    writer.writerow(['length', 'maturity', 'x', 'y', 'width', 'height', 'image_name', 'ID', 'Alternative view ID', 'position', 'event', 'net', 'board'])
    krill = Krill.objects.filter(unique_krill_id__contains=trip).values('length', 'maturity', 'x', 'y', 'width',
                                                                        'height', 'image_file_id', 'lateral', 'dorsal', 'unique_krill_id', 'altr_view', 'position', 'altr_height', 'altr_width',
                                                                        'altr_x', 'altr_y', 'event', 'net', 'board')
    krill = list(krill)
    # print(krill)
    for row in krill:
        if (row['maturity'] != "Unclassified"):
            # x=int(row['x'])
            # y=int(row['y'])
            # w=int(row['width'])
            # h=int(row['height'])3
            # image = Image.objects.get(file_name=row['image_file_id'])
            # image = cv2.imread("media/"+str(image.image))
            # image = image[y:y+h,x:x+w]
            altID = row['unique_krill_id'].split('-')[-1]
            altID = row['altr_view'].split('/')[-1] + '-' + altID
            writer.writerow(
                [row['length'], row['maturity'], row['x'], row['y'], row['width'], row['height'],
                 row['image_file_id'], row['unique_krill_id'], altID, row['position'], row['event'], row['net'], row['board']])

    SUBJECT = 'Subject string'
    FILENAME = str(trip) + '.csv'
    MY_EMAIL = 'uea.krill.annotation@gmail.com'
    MY_PASSWORD = 'Krill123'
    TO_EMAIL = eml
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587

    msg = MIMEMultipart()
    msg['From'] = MY_EMAIL
    msg['To'] = COMMASPACE.join([TO_EMAIL])
    msg['Subject'] = SUBJECT

    part = MIMEBase('application', "octet-stream")
    part.set_payload(csvfile.getvalue())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=FILENAME)
    msg.attach(part)
    smtpObj = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.login(MY_EMAIL, MY_PASSWORD)
    smtpObj.sendmail(MY_EMAIL, TO_EMAIL, msg.as_string())
    smtpObj.quit()


def Sort_Boxes(request):
    list = []
    MAGIC_NUMBER = 550
    image = Image.objects.get(image=str(request.POST['image_file']))
    image = cv2.imread("media/" + str(image.image))
    bounding_boxes = request.POST['image_annotations']
    # Removing the square brackets and quotations from the string
    bounding_boxes = bounding_boxes[2:]
    bounding_boxes = bounding_boxes[:-2]
    # Split the string into individual annotations
    bounding_boxes = bounding_boxes.split('","')
    for i in bounding_boxes:
        list.append(ast.literal_eval(i.replace("\\", "")))

    sorted_ctrs = sorted(list, key=lambda box: box['x'] * MAGIC_NUMBER + box['y'] * image.shape[1])

    return JsonResponse({
        'annotations': sorted_ctrs,
    })


def Detect_Krill(request):
    FAST = True
    # load in the foreground and ratio histogram classes
    image = str(os.path.join(settings.MEDIA_ROOT, str(request.POST['image_file'])))
    foregroundHist = scipy.io.loadmat(
        str(os.path.join(settings.STATIC_ROOT, 'MatlabFiles//normalisedForeground32.mat')))
    ratioHist = scipy.io.loadmat(str(os.path.join(settings.STATIC_ROOT, 'MatlabFiles//ratioHistogram32.mat')))
    histograms32 = HistogramConfig(foregroundHist, ratioHist, 32)
    print("Normalising Image\n")
    # newKrillImage = img_normalise(image)
    newKrillImage = img_normalise(image)
    print("Applying Logical Mask\n")
    logical_mask = segmentKrill(newKrillImage, histograms32, FAST)
    print("Performing Opening and Closing\n")
    noiseReducedmask = performOpeningClosing(logical_mask)
    print("Superimposing Bounding Boxes\n")
    regions = createBoundingBoxes(noiseReducedmask, image)
    return JsonResponse({
        'annotations': regions,
    })


##
##
##      KRILL DETECTION OPERATIONS
##
##

class HistogramConfig:
    # so here we have the default parameters for the testing class
    # otherwise we siply take the passed parameters
    # this is defined as the instance variable
    def __init__(self, foregroundHist, ratioHist, quantLevel=32):
        self.foregroundHist = foregroundHist
        self.ratioHist = ratioHist
        self.quantLevel = quantLevel


# here we want to be able to find the bounding boxes based on the binary image
# x,y,w,h = cv2.boundingRect(cnt) where (x, y) is top - left point and (w, h) is the width and height
def createBoundingBoxes(img, original_image_path):
    # first argument - source image, second argument -  contours to be drawn as a python list
    # 3rd argument index of contours
    # remaining arguments - colour and thickness
    # cv2.drawContours(original_img, [rectangle], -1, (0, 0, 255), 3)
    # Contours contains the rough co-ordinates of our contours.
    contours = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    # manually tuned offset, weighting the x-axis order.
    MAGIC_NUMBER = 550

    original_img = cv2.imread(original_image_path, cv2.IMREAD_COLOR)

    num_contours = len(contours)

    mean_area = 0

    max_area = 0

    for i in range(0, num_contours):
        if cv2.contourArea(contours[i]) > max_area:
            max_area = cv2.contourArea(contours[i])
        mean_area += cv2.contourArea(contours[i])

    mean_area = max_area

    # way of going through each contour

    regions = []
    bbs = []
    # sort the bounding boxes to match sophie's conventions
    sorted_ctrs = sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[0] * MAGIC_NUMBER + cv2.boundingRect(ctr)[1] *
                                                   original_img.shape[1])

    # sorted_ctrs = sorted(contours, key=lambda ctr: cv2.boundingRect(ctr)[0]  * original_img.shape[1])

    for i in range(0, num_contours):
        if not (smallCountourCheck(sorted_ctrs[i], mean_area)):
            # xCoord,yCoord,w,h = cv2.boundingRect(contours[i])
            box = cv2.boundingRect(sorted_ctrs[i])
            box = {
                "name": "rect",
                "x": box[0],
                "y": box[1],
                "width": box[2],
                "height": box[3]
            }
            regions.append(box)

    # print(regions)
    # rectangle = cv2.rectangle(original_img, (x,y), (x+w, y+h), (0, 0, 255), 5)
    # test = sorted(bbs,key=lambda b:b[1][i],reverse=False)

    return regions


#
# Method to remove very small contour
#
def smallCountourCheck(c, mean):
    return cv2.contourArea(c) < (0.5 * mean / 10)


# function to perform opening and closing
# might need to use a different structuring element ?
def performOpeningClosing(logicalImg):
    firstKernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))

    secondKernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (26, 26))

    opening = cv2.morphologyEx(logicalImg, cv2.MORPH_DILATE, firstKernel)

    closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, secondKernel)

    # cv2.namedWindow("output", cv2.WINDOW_NORMAL)
    # newImg = cv2.resize(closing, (6048, 4032))
    # cv2.imshow("output", newImg)
    # cv2.waitKey(0)

    return closing


# this function is designed to take a normalised image and the respective histogram object
def segmentKrill(normalisedImg, histogram_object, FAST):
    qLevels = histogram_object.quantLevel

    # pre-calculated threshold values
    GENERIC_THRESHOLD = 1000.0
    GENERIC_THREHOLD_FOREGROUND = 0.00001

    # logical matrix for segmented image
    logicalImg = cv2.cvtColor(normalisedImg, cv2.COLOR_BGR2GRAY)

    # get the float representation
    # floatRep =  normalisedImg.astype(float)

    # new quantised image
    normalisedImg[:, :, 0] = (normalisedImg[:, :, 0] / 255 * qLevels)
    normalisedImg[:, :, 1] = (normalisedImg[:, :, 1] / 255 * qLevels)
    normalisedImg[:, :, 2] = (normalisedImg[:, :, 2] / 255 * qLevels)

    if not FAST:

        dimensions_tuple = normalisedImg.shape

        for i in range(0, dimensions_tuple[0]):
            for x in range(0, dimensions_tuple[1]):

                bValue = normalisedImg.item(i, x, 0)
                gValue = normalisedImg.item(i, x, 1)
                rValue = normalisedImg.item(i, x, 2)

                # need to decrement pixel index due to python conventions of starting from 0
                ratioProb = histogram_object.ratioHist['ratioHist32Final'][rValue - 1][gValue - 1][bValue - 1]
                foregroundProb = histogram_object.foregroundHist['normalisedHistogramB'][rValue - 1][gValue - 1][
                    bValue - 1]

                if ratioProb > GENERIC_THRESHOLD and foregroundProb > GENERIC_THREHOLD_FOREGROUND:
                    logicalImg.itemset((i, x), 255)
                else:
                    logicalImg.itemset((i, x), 0)
    else:

        foregroundHist = histogram_object.foregroundHist['normalisedHistogramB']
        ratioHistogram = histogram_object.ratioHist['ratioHist32Final']

        # we want to index the histogram based on the BGR combonations of the
        # normalised image, with isolated channels
        # B channel
        first_index = np.clip((normalisedImg[:, :, 0]) - 1, 0, 31)
        # G Channel
        second_index = np.clip((normalisedImg[:, :, 1]) - 1, 0, 31)
        # R channel
        third_index = np.clip((normalisedImg[:, :, 2]) - 1, 0, 31)

        dimensions = logicalImg.shape

        foreground_probabilities_pixels = np.zeros(dimensions, dtype='float64')

        ratio_probabilities_pixels = np.zeros(dimensions, dtype='float64')

        foreground_probabilities_pixels[:, :] = foregroundHist[third_index, second_index, first_index]

        ratio_probabilities_pixels[:, :] = ratioHistogram[third_index, second_index, first_index]

        foreground_thresh = foreground_probabilities_pixels > GENERIC_THREHOLD_FOREGROUND
        foreground_second_thresh = foreground_probabilities_pixels < GENERIC_THREHOLD_FOREGROUND

        ratio_thresh = ratio_probabilities_pixels > GENERIC_THRESHOLD
        ratio_second_thresh = ratio_probabilities_pixels < GENERIC_THRESHOLD

        foreground_probabilities_pixels[foreground_thresh] = 255
        foreground_probabilities_pixels[foreground_second_thresh] = 0

        ratio_probabilities_pixels[ratio_thresh] = 255
        ratio_probabilities_pixels[ratio_second_thresh] = 0

        logical_combine = np.logical_and(ratio_thresh, foreground_thresh)
        logical_second_combine = np.logical_and(ratio_second_thresh, foreground_second_thresh)

        ratio_probabilities_pixels[logical_combine] = 255
        ratio_probabilities_pixels[logical_second_combine] = 0

        # logicalImg = np.where(final_threshold, foreground_probabilities_pixels, ratio_probabilities_pixels)

        logicalImg = ratio_probabilities_pixels.astype('uint8')

    return logicalImg


# take an img path and return the read in img
# read in colour image
def read_img(imgPath):
    img = cv2.imread(imgPath, cv2.IMREAD_COLOR)
    cv2.imshow('image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return img


# method to noramlise an image
def img_normalise(imgPath):
    # is read in as B G R
    img = cv2.imread(imgPath, cv2.IMREAD_COLOR)

    # load in the pre-pickled reference RGB array
    # convert to float for later operations
    ref_RGB = scipy.io.loadmat(str(os.path.join(settings.STATIC_ROOT, 'MatlabFiles//MeanColourReference.mat')))
    ref_colours = ref_RGB['meanColourRef']

    # blue = red, green = green, red = blue
    # this is the extracted colour channels for the image in question
    blue = img[:, :, 0]
    green = img[:, :, 1]
    red = img[:, :, 2]

    green_avg = np.mean(green)
    red_avg = np.mean(red)
    blue_avg = np.mean(blue)

    # for blue channel we essentially need to cap the limit to 255. So must go through manually
    img[:, :, 0] = np.clip((blue / blue_avg) * ref_colours[0, 2], 0, 255)
    img[:, :, 1] = np.clip((green / green_avg) * ref_colours[0, 1], 0, 255)
    img[:, :, 2] = np.clip((red / red_avg) * ref_colours[0, 0], 0, 255)

    # cv2.namedWindow("output", cv2.WINDOW_NORMAL)
    # newImg = cv2.resize(img, (6048, 4032))
    # cv2.imshow("output", newImg)
    # cv2.waitKey(0)

    return img


# need to manually set yhe value to be 255
def calculatePixelValue(currentPixelValue, avg, ref_colour):
    value = round((currentPixelValue / avg) * ref_colour)
    if value > 255:
        return 255
    else:
        return value


# method to save an item with a filename
def pickle_item(fileName, item2Pickle):
    # write to the objectDump.text file
    with open(fileName, 'wb') as f:
        pickle.dump(item2Pickle, f, pickle.DEFAULT_PROTOCOL)


# method to load an item based on the filepath
def load_item(filePath):
    with open(filePath, 'rb') as f:
        return pickle.load(f)
