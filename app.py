from flask import Flask, request, jsonify
import re
import easyocr 
from PIL import Image
import io
import numpy as np
import pytesseract
from PIL import Image, ImageFilter

app = Flask(__name__)


reader = easyocr.Reader(['en']) 


#--------------------Facebook-----------------------------------------------
def convert_to_number(value):
    value = value.lower()
    if value.endswith('m'):
        return int(float(value[:-1]) * 1000000)
    elif value.endswith('k'):
        return int(float(value[:-1]) * 1000)
    return int(value)


@app.route('/facebook/', methods=['POST'])
def extract_text_fb():
    try:
        image_file = request.files['image']
        jobId = request.form.get('jobId')
        postType = request.form.get('postType', 'post')
        dataType = request.form.get('dataType', 'all')

        if image_file:
            image = image_file.read()
            results = reader.readtext(image)

            extracted_text = ' '.join(result[1] for result in results)

            if postType == 'post':
                #Likes
                likes_match = re.search(r'(\d+(?:\.\d+)?[Kk])\s+?(\d+)\s+comments?', extracted_text, re.IGNORECASE)
                if likes_match is None:
                    likes_match = re.search(r'(\d+(?:\.\d+)?[Mm]?)\s+?(\d+(?:\.\d+)?[Kk]?)\s+comments?', extracted_text, re.IGNORECASE)
                    
                if likes_match is None:
                    likes_match = re.search(r'(\d+)\s+others', extracted_text, re.IGNORECASE)
                    
                if likes_match is None:
                    likes_match = re.search(r'(\d+)\s+?(\d+)\s+comments?', extracted_text, re.IGNORECASE)
                
                #Comments  
                comments_match = re.search(r'(\d+)\s+comments?', extracted_text, re.IGNORECASE)
                if comments_match is None:
                    comments_match = re.search(r'(\d+)\s+?(\d+)\s+comments?', extracted_text, re.IGNORECASE)
                    
                if comments_match is None:
                    comments_match = re.search(r'(\d+(?:\.\d+)?[Kk]?)\s+comments?', extracted_text, re.IGNORECASE)
                
                #Shares  
                shares_match = re.search(r'(\d+)\s+shares?', extracted_text, re.IGNORECASE)
                if shares_match is None:
                    shares_match = re.search(r'(\d+(?:\.\d+)?[Kk]?)\s+shares?', extracted_text, re.IGNORECASE)
                
                #Views
                views_match = re.search(r'(\d+(?:\.\d+)?[Kk]?)\s+views?', extracted_text, re.IGNORECASE)

                response_data = {
                    'JobId' : jobId,
                    'text': extracted_text,
                }
                
                if dataType == 'likes':
                    response_data['likes'] = convert_to_number(likes_match.group(1)) if likes_match else 0
                elif dataType == 'comments':
                    response_data['comments'] = convert_to_number(comments_match.group(1)) if comments_match else 0
                elif dataType == 'shares':
                    response_data['shares'] = convert_to_number(shares_match.group(1)) if shares_match else 0,
                elif dataType == 'views':
                    response_data['views'] = convert_to_number(views_match.group(1)) if views_match else 0
                else:
                    response_data['likes'] = convert_to_number(likes_match.group(1)) if likes_match else 0,
                    response_data['comments'] = convert_to_number(comments_match.group(1)) if comments_match else 0,
                    response_data['shares'] = convert_to_number(shares_match.group(1)) if shares_match else 0,
                    response_data['views'] = convert_to_number(views_match.group(1)) if views_match else 0
                

            elif postType == 'story':
                #Views
                views_match = re.search(r'(\d+)\s+viewers?', extracted_text, re.IGNORECASE)
                if views_match is None:
                    views_match = re.search(r'(\d+(?:\.\d+)?[Kk]?)\s+viewers?', extracted_text, re.IGNORECASE)

                response_data = {
                    'JobId' : jobId,
                    'text': extracted_text,
                }
                
                if dataType == 'views':
                    response_data['views'] = convert_to_number(views_match.group(1)) if views_match else 0
                else:
                    response_data['views'] = convert_to_number(views_match.group(1)) if views_match else 0

            else:
                return jsonify({'error': 'Invalid postType'}), 400

            return jsonify(response_data)
        else:
            return jsonify({'error': 'No image file provided'}), 400

    except:
        return jsonify({'error': 'Please Select correct SocialMedia Image.'}), 400




#--------------Instagram--------------------------------------------------
def parse_count(count_str):
    if 'K' in count_str:
        return int(float(count_str.replace('K', 'e3').replace(',', '')))
    elif 'M' in count_str:
        return int(float(count_str.replace('M', 'e6').replace(',', '')))
    else:
        return int(count_str.replace(',', ''))

@app.route('/instagram/', methods=['POST'])
def extract_text_instagram():
    try:
        job_id = request.form.get('jobId')
        post_type = request.form.get('postType')
        data_type = request.form.get('dataType')

        if post_type == 'post':
            return extract_text_insta(job_id, data_type)
        elif post_type == 'story':
            return extract_text_story(job_id, data_type)
        elif post_type == 'reel':
            return extract_text_reel(job_id, data_type)
        else:
            return jsonify({'error': 'Invalid postType'}), 400

    except:
        return jsonify({'error': 'Please Select Correct PostType'}), 400


def extract_text_insta(job_id, data_type):
    try:
        image_file = request.files['image']

        if image_file:
            image = image_file.read()
            results = reader.readtext(image)

            extracted_text = ' '.join(result[1] for result in results)

            if data_type == 'likes':
                likes_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:,\d+)*)\s+others', extracted_text)
                likes_match_only = re.search(r'(\d{1,3}(?:,\d{3})*)\s+[lL]ikes', extracted_text)

                if likes_match:
                    total_likes = int(likes_match.group(1).replace(',', '')) + 1
                    response_data = {
                        'jobId': job_id,
                        'likes': total_likes
                    }
                elif likes_match_only:
                    response_data = {
                        'jobId': job_id,
                        'likes': likes_match_only.group(1).strip('"')
                    }
                else:
                    response_data = {
                        'jobId': job_id,
                        'likes': 0
                    }
            elif data_type == 'comments':
                comments_match = re.search(r'(\d+(,\d+)?)\s+comments?', extracted_text, re.IGNORECASE)
                comments_count = comments_match.group(1).replace(',', '') if comments_match else '0'
                response_data = {
                    'jobId': job_id,
                    'comments': int(comments_count),
                }
            else:
                return jsonify({'error': 'Invalid dataType'}), 400

            response_data['text'] = extracted_text
            return jsonify(response_data)
        else:
            return jsonify({'error': 'No image file provided'}), 400

    except:
        return jsonify({'error': 'Please Select correct SocialMedia Image.'}), 400


def extract_text_story(job_id, data_type):
    try:
        image_file = request.files['image']

        if image_file:
            uploaded_file = image_file

            if not uploaded_file.filename.endswith(('.jpg', '.jpeg', '.png')):
                return jsonify({'error': 'Invalid file format'}), 400

            img = Image.open(uploaded_file)

            left, top, right, bottom = 0, 40, 200, 700

            cropped_img = img.crop((left, top, right, bottom))

            img_byte_array = io.BytesIO()
            cropped_img.save(img_byte_array, format="PNG")
            img_bytes = img_byte_array.getvalue()

            result = reader.readtext(img_bytes)

            extracted_numbers = []
            # extracted_text = []
            
            for item in result:
                text = item[1]
                
                numbers_with_commas = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', text)
                
                for num in numbers_with_commas:
                    num = num.replace(',', '')
                    if '.' in num:
                        extracted_numbers.append(float(num))
                    else:
                        extracted_numbers.append(int(num))
                
                # extracted_text.append(text)

            if extracted_numbers:
                extracted_number = max(extracted_numbers)
            else:
                extracted_number = 0

            response_data = {
                'jobId': job_id,
                'Views': extracted_number,
                # 'ExtractedText': extracted_text
            }

            return jsonify(response_data)
        else:
            return jsonify({'error': 'No image file provided'}), 400

    except:
        return jsonify({'error': 'Please Select correct SocialMedia Image.'}), 400


def extract_text_reel(job_id, data_type):
    try:
        image_file = request.files['image']

        if image_file:
            uploaded_file = image_file

            if not uploaded_file.filename.endswith(('.jpg', '.jpeg', '.png')):
                return jsonify({'error': 'Invalid file format'}), 400

            img = Image.open(uploaded_file)

            left, top, right, bottom = img.width - 200, 100, img.width, 1300

            cropped_img = img.crop((left, top, right, bottom))

            img_byte_array = io.BytesIO()
            cropped_img.save(img_byte_array, format="PNG")
            img_bytes = img_byte_array.getvalue()

            result = reader.readtext(img_bytes)

            extracted_text = [item[1] for item in result]

            if data_type == 'likes':
                response_data = {
                    'jobId': job_id,
                    'likes': parse_count(extracted_text[0]),
                }
            elif data_type == 'comments':
                response_data = {
                    'jobId': job_id,
                    'comments': parse_count(extracted_text[1]),
                }
            elif data_type == 'shares':
                response_data = {
                    'jobId': job_id,
                    'shares': parse_count(extracted_text[2]),
                }
            else:
                return jsonify({'error': 'Invalid dataType'}), 400

            return jsonify(response_data)
        else:
            return jsonify({'error': 'No image file provided'}), 400

    except:
        return jsonify({'error': 'Please Select correct SocialMedia Image.'}), 400




#------------------------------Snapchat--------------------------------

@app.route('/snapchat/', methods=['POST'])
def extract_text_snapchat():
    try:
        job_id = request.form.get('jobId')
        post_type = request.form.get('postType')
        data_type = request.form.get('dataType')

        if post_type == 'story':
            return snapchat_story(job_id, data_type)
        elif post_type == 'spotlight':
            return snapchat_spotlight(job_id, data_type)
        else:
            return jsonify({'error': 'Invalid postType'}), 400
        

    except:
        return jsonify({'error': 'Please Select Correct PostType'}), 400


@app.route('/snapchat-story/', methods=['POST'])
def snapchat_story(job_id, data_type):
    try:
        response_data = {}

        image_file = request.files['image']

        if image_file:
            image = image_file.read()
            results = reader.readtext(image)

            extracted_text = ' '.join(result[1] for result in results)
            
            if data_type == 'views':
            # Views
                views_match = re.search(r'(\d+(?:\.\d+)?[Kk]?)\s+views?', extracted_text, re.IGNORECASE)

            if views_match:
                response_data['views'] = convert_to_number(views_match.group(1))
            else:
                response_data['views'] = 0

        response_data['text'] = extracted_text
        response_data['jobId'] = job_id

        return jsonify(response_data), 200
    except:
        return jsonify({'error': 'Please Select correct SocialMedia Image.'}), 400



@app.route('/snapchat-spotlight/', methods=['POST'])
def snapchat_spotlight(job_id, data_type):
    try:
        image_file = request.files.get('image')

        if not image_file:
            return jsonify({'error': 'No image file provided'}), 400

        if not image_file.filename.endswith(('.jpg', '.jpeg', '.png')):
            return jsonify({'error': 'Invalid file format'}), 400

        image_bytes = image_file.read()

        img = Image.open(io.BytesIO(image_bytes))

        # Crop the first rectangle (right side)
        left1, top1, right1, bottom1 = img.width - 200, 300, img.width, 1450
        cropped_img1 = img.crop((left1, top1, right1, bottom1))

        # Crop the second rectangle (left side)
        left2, top2, right2, bottom2 = 0, 300, 150, 1450
        cropped_img2 = img.crop((left2, top2, right2, bottom2))

        buffered1 = io.BytesIO()
        cropped_img1.save(buffered1, format="PNG")

        buffered2 = io.BytesIO()
        cropped_img2.save(buffered2, format="PNG")

        reader = easyocr.Reader(['en'])
        result1 = reader.readtext(np.array(cropped_img1))
        result2 = reader.readtext(np.array(cropped_img2))
        
        print("Result1 (before conversion):", [item[1] for item in result1])
        print("Result2 (before conversion):", [item[1] for item in result2])

        extracted_text1 = [convert_to_number(item[1]) for item in result1 if re.match(r'^\d+(\.\d+)?[MK]?$', item[1], re.I)]
        extracted_text2 = [convert_to_number(item[1]) for item in result2 if re.match(r'^\d+(\.\d+)?[MK]?$', item[1], re.I)]

        print("Extracted and Converted Text 1:", extracted_text1)
        print("Extracted and Converted Text 2:", extracted_text2)

        response_data = {}
        
        if data_type == 'comments':
            if len(extracted_text1) >= 1:
                response_data['comments'] = extracted_text1[0]
            else:
                return jsonify({'error': 'No comments found'}), 400
        elif data_type == 'shares':
            if len(extracted_text1) >= 2:
                response_data['shares'] = extracted_text1[1]
            else:
                return jsonify({'error': 'No shares found'}), 400
        elif data_type == 'views':
            if len(extracted_text2) >= 1:
                response_data['views'] = extracted_text2[0]
            else:
                return jsonify({'error': 'No views found'}), 400
        elif data_type == 'likes':
            if len(extracted_text2) >= 2:
                response_data['likes'] = extracted_text2[1]
            else:
                return jsonify({'error': 'No likes found'}), 400
        else:
            return jsonify({'error': 'Invalid dataType'}), 400

        response_data['jobId'] = job_id
        
        return jsonify(response_data), 200
    except:
        return jsonify({'error': 'Please Select correct SocialMedia Image.'}), 400
    


#------------------Linkedin----------------------------

@app.route('/linkedin/', methods=['POST'])
def extract_text_linkedin():
    try:
        image_file = request.files['image']
        job_id = request.form.get('jobId')
        postType = request.form.get('postType', 'post')
        dataType = request.form.get('dataType', 'all')

        if image_file:
            # image = image_file.read()
            image = Image.open(image_file)
            
            extracted_text_linkedin = pytesseract.image_to_string(image, lang='eng')
            extracted_text_linkedin = extracted_text_linkedin.replace('\n', ' ')
    
            if postType == 'post':
                #Likes
                likes_match = re.search(r'([\d,]+)\s+others', extracted_text_linkedin, re.IGNORECASE)
                if likes_match is None:
                    likes_match = re.search(r'([\d,]+)\s+?(\d+)\s+comments?', extracted_text_linkedin, re.IGNORECASE)

                #Comments  
                comments_match = re.search(r'([\d,]+)\s+comments?', extracted_text_linkedin, re.IGNORECASE)
                if comments_match is None:
                    comments_match = re.search(r'(\d+)\s+comment?', extracted_text_linkedin, re.IGNORECASE)
                
                #Reposts  
                reposts_match = re.search(r'([\d,]+)\s+reposts?', extracted_text_linkedin, re.IGNORECASE)
                if reposts_match is None:
                    reposts_match = re.search(r'(\d+)\s+repost?', extracted_text_linkedin, re.IGNORECASE)
                    
                #Impression  
                impressions_match = re.search(r'([\d,]+)\s+impressions?', extracted_text_linkedin, re.IGNORECASE)
                if impressions_match is None:
                    impressions_match = re.search(r'(\d+)\s+impressions?', extracted_text_linkedin, re.IGNORECASE)

                response_data = {
                    'jobId' : job_id,
                    'text': extracted_text_linkedin,
                }
                
                if dataType == 'likes':
                    response_data['likes'] = convert_to_number(likes_match.group(1).replace(',', '')) if likes_match else 0 
                elif dataType == 'comments':
                    response_data['comments'] = convert_to_number(comments_match.group(1).replace(',', '')) if comments_match else 0
                elif dataType == 'reposts':
                    response_data['reposts'] = convert_to_number(reposts_match.group(1).replace(',', '')) if reposts_match else 0
                elif dataType == 'impressions':
                    response_data['impressions'] = convert_to_number(impressions_match.group(1).replace(',', '')) if impressions_match else 0
                else:
                    response_data['likes'] = convert_to_number(likes_match.group(1).replace(',', '')) if likes_match else 0
                    response_data['comments'] = convert_to_number(comments_match.group(1).replace(',', '')) if comments_match else 0
                    response_data['reposts'] = convert_to_number(reposts_match.group(1).replace(',', '')) if reposts_match else 0
                    response_data['impressions'] = convert_to_number(impressions_match.group(1).replace(',', '')) if impressions_match else 0
                    
            else:
                return jsonify({'error': 'Invalid postType'}), 400
                
            return jsonify(response_data)
        else:
            return jsonify({'error': 'No image file provided'}), 400
    except:
        return jsonify({'error': 'Please Select correct SocialMedia Image.'}), 400


#Twitter
@app.route('/twitter/', methods=['POST'])
def extract_text_twitter():
    image_file = request.files['image']

    if image_file:
        image = Image.open(image_file)
        
        extracted_text_detections = reader.readtext(image)

        extracted_text = " ".join([detection[1] for detection in extracted_text_detections])

        # Likes
        likes_match = re.search(r'([\d,]+)\s+likes', extracted_text, re.IGNORECASE)
        if likes_match is None:
            likes_match = re.search(r'(\d+(?:\.\d+)?[KkMm]?)\s+likes?', extracted_text, re.IGNORECASE)
        
        # Views
        views_match = re.search(r'([\d,]+)\s+views', extracted_text, re.IGNORECASE)
        if views_match is None:
            views_match = re.search(r'(\d+(?:\.\d+)?[KkMm]?)\s+views?', extracted_text, re.IGNORECASE)

        # Comments
        comments_match = re.search(r'([\d,]+)\s+comments?', extracted_text, re.IGNORECASE)

        # Reposts
        reposts_match = re.search(r'([\d,]+)\s+reposts?', extracted_text, re.IGNORECASE)
        if reposts_match is None:
            reposts_match = re.search(r'(\d+(?:\.\d+)?[KkMm]?)\s+reposts?', extracted_text, re.IGNORECASE)

        # Impressions
        impressions_match = re.search(r'impressions\s+([\d,]+)', extracted_text, re.IGNORECASE)
        if impressions_match is None:
            impressions_match = re.search(r'([\d,]+)\s+impressions?', extracted_text, re.IGNORECASE)
            
        # Engagements
        engagements_match = re.search(r'engagements\s+([\d,]+)', extracted_text, re.IGNORECASE)
        if engagements_match is None:
            engagements_match = re.search(r'([\d,]+)\s+engagements?', extracted_text, re.IGNORECASE)

        response_data = {
            'text': extracted_text,
            'likes': convert_to_number(likes_match.group(1).replace(',', '')) if likes_match else 0,
            'views': convert_to_number(views_match.group(1).replace(',', '')) if views_match else 0,
            'comments': convert_to_number(comments_match.group(1).replace(',', '')) if comments_match else 0,
            'reposts': convert_to_number(reposts_match.group(1).replace(',', '')) if reposts_match else 0,
            'impressions': convert_to_number(impressions_match.group(1).replace(',', '')) if impressions_match else 0,
            'engagements': convert_to_number(engagements_match.group(1).replace(',', '')) if engagements_match else 0
        }

        return jsonify(response_data)
    else:
        return jsonify({'error': 'No image file provided'}), 400


import base64
@app.route('/test/', methods=['POST'])
def perform_ocr():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'})

    image = request.files['image']

    if image:
        image_bytes = image.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = Image.open(io.BytesIO(nparr))

        width, height = img.size
        left, top, right, bottom = 0, 3 * height // 4, width, height

        cropped_img = img.crop((left, top, right, bottom))

        results = reader.readtext(np.array(cropped_img))

        recognized_text = ' '.join([result[1] for result in results])
        
        number_match = re.search(r'[1-9]\d*(,\d{3})*(\.\d+)?', recognized_text)

        if number_match:
            matched_number = number_match.group().replace(',', '')
            first_number = int(matched_number)
        else:
            first_number = None

        response_data = {
            'text': recognized_text,
            'comments': first_number
        }

        buffered = io.BytesIO()
        cropped_img.save(buffered, format="JPEG")
        cropped_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        # response_data['cropped_image'] = cropped_image_base64

        return jsonify(response_data)
    else:
        return jsonify({'error': 'Invalid image format'})



if __name__ == '__main__':
    app.run(debug=True, port=3000)
