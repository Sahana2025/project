from django.shortcuts import render, redirect
from django.conf import settings
from .forms import UserImageForm
from .models import UserImage
from google.cloud import vision
import openai

# Set Groq API credentials
openai.api_key = settings.GROQ_API_KEY
openai.api_base = "https://api.groq.com/openai/v1"

# 1. INDEX PAGE VIEW
def index(request):
    return render(request, 'index.html')  # You already added "Get Started" button here


# 2. CHOOSE CATEGORY PAGE VIEW
def choose_category(request):
    return render(request, 'choose_category.html')  # Has 3 cards: plant, animal, human


# 3. COMMON IMAGE ANALYSIS FUNCTION
def analyze_image_with_vision(image_path, category):
    client = vision.ImageAnnotatorClient()
    with open(image_path, 'rb') as img_file:
        content = img_file.read()
    image = vision.Image(content=content)
    response = client.label_detection(image=image)
    labels = [label.description.lower() for label in response.label_annotations]
    print("Google Vision labels:", labels)
    if not labels:
        return "❌ No clear content found in the image. Please try again."

    keywords = {
        'plant': ['plant', 'leaf', 'tree', 'flower', 'stem', 'root', 'vegetable', 'fruit'],
        'animal': ['animal', 'dog', 'cat', 'cow', 'goat', 'rabbit', 'sheep', 'horse', 'mammal'],
        'human': ['human', 'person', 'fever', 'headache', 'cold', 'pain', 'symptom', 'body','girl','boy','person', 'face', 'hand', 'skin', 'human', 'body', 'arm', 'leg','neck', 'facial expression', 'throat', 'flesh'],

    }

    if not any(keyword in labels for keyword in keywords[category]):
        return f"🚫 This image doesn't seem to be related to **{category}**. Please upload a relevant image."

    label_text = ", ".join(labels[:10])
    ai_response = openai.ChatCompletion.create(
        model="mistral-saba-24b",
        messages=[
            {"role": "system", "content": f"You are a helpful {category} disease expert. Based on image labels, give a diagnosis and remedy in 2–3 lines. Do not mention the labels."},
            {"role": "user", "content": f"The image shows: {label_text}. What is the diagnosis and remedy?"}
        ]
    )

    return ai_response.choices[0].message.content.strip()


# 4. SHARED CHATBOT HANDLER VIEW
def handle_chat(request, category, greeting, keyword_list, system_prompt):
    user_message = None
    bot_reply = None
    image_url = None

    if request.method == 'POST':
        if 'image' in request.FILES:
            form = UserImageForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.save()
                image_url = image.image.url
                bot_reply = analyze_image_with_vision(image.image.path, category)
            else:
                bot_reply = "❌ Invalid image upload. Please try again."
        else:
            user_message = request.POST.get('message', '')
            greetings = ['hi', 'hello', 'hey', 'good morning', 'good evening']
            if any(greet in user_message.lower() for greet in greetings):
                bot_reply = greeting
            elif any(word in user_message.lower() for word in keyword_list):
                response = openai.ChatCompletion.create(
                    model="mistral-saba-24b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                )
                bot_reply = response.choices[0].message.content.strip()
            else:
                bot_reply = f"🤖 I'm only trained for **{category}**-related topics. Please ask relevant questions."

    return render(request, f'{category}_chat.html', {
    'user_message': "",  # clear it here
    'bot_reply': bot_reply,
    'image_url': image_url
})



# 5. PLANT CHATBOT VIEW
def plant_chat(request):
    return handle_chat(
        request,
        category='plant',
        greeting="🌿 Hello! I'm your Plant Health Assistant. How can I help with your plant today?",
        keyword_list=['plant', 'leaf', 'tree', 'flower', 'fruit', 'root', 'stem', 'spot', 'wilt'],
        system_prompt="You are a helpful plant doctor. Reply in max 3 lines with a short diagnosis and one remedy."
    )


# 6. ANIMAL CHATBOT VIEW
def animal_chat(request):
    return handle_chat(
        request,
        category='animal',
        greeting="🐾 Hello! I'm your Animal Health Assistant. How can I help with your pet or livestock?",
        keyword_list=['dog', 'cat', 'animal', 'cow', 'sheep', 'goat', 'pet'],
        system_prompt="You are a helpful veterinary expert. Reply in max 3 lines with a short diagnosis and treatment."
    )


# 7. HUMAN CHATBOT VIEW
def human_chat(request):
    return handle_chat(
        request,
        category='human',
        greeting="🧍 Hello! I'm your Health Assistant. Ask me about any human symptoms or conditions.",
        keyword_list=['human', 'person', 'fever', 'headache', 'cold', 'pain', 'symptom', 'body','girl','boy','person', 'face', 'hand', 'skin', 'human', 'body', 'arm', 'leg','neck', 'facial expression', 'throat', 'flesh'],

        system_prompt="You are a friendly medical expert. Provide short, accurate advice in max 3 lines.",

    )
   
