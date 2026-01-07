import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
import random
import re
import numpy as np
from PIL import Image
import io
import math
import hashlib
import secrets

# Alkalmazás konfiguráció
def setup_page_config():
    st.set_page_config(page_title="Quiz Alkalmazás", layout="wide")

# Mappastruktúra
QUIZ_RESULTS_DIR = "quiz_results"
QUIZ_CONFIG_FILE = "quiz_config.json"
QUIZZES_DIR = "quizzes"
IMAGES_DIR = "quiz_images"
STUDENTS_FILE = "students.json"


def gen_task(api_key, task_name, task_topic, num_of_task, ai_teacher_desc):
    from google import genai
    config = load_config()

    client = genai.Client(api_key=api_key)




    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="""Csinálj json formátumban egy feladatsort ilyen formában:
        [
            {
                "question": "Oldd meg az egyenletet: 0.5x + 2 = 3x - 1",
                "type": "text",
                "answer": ["1.2"],
                "points": 1,
                "match_type": "number"
            }
        ]
        ,"""+ f"{config['prompt']['resz1']}: "+ task_topic+f"{config['prompt']['resz2']}"+ num_of_task+ f"{config['prompt']['resz3']} "+ai_teacher_desc+f". {config['prompt']['resz4']}",
    )
    with open(f"quizzes/{task_name}.json", "w") as f:
        f.write(response.text[7:-3])

# Jelszó kezelés
def hash_password(password):
    """Jelszó hash-elése"""
    salt = secrets.token_hex(16)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() + ":" + salt

def simple_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Jelszó ellenőrzése"""
    try:
        hashed_pw, salt = hashed.split(":")
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex() == hashed_pw
    except:
        return False

def verify_teacher_password(password):
    """Tanári jelszó ellenőrzése"""
    config = load_config()
    teacher_hash = config.get("teacher_password_hash")
    if not teacher_hash:
        default_password = "tanar123"
        if password == default_password:
            config["teacher_password_hash"] = hash_password(default_password)
            save_config(config)
            return True
        return False
    return verify_password(password, teacher_hash)

def change_teacher_password(old_password, new_password):
    """Tanári jelszó megváltoztatása"""
    if not verify_teacher_password(old_password):
        return False, "Hibás régi jelszó"
    
    config = load_config()
    config["teacher_password_hash"] = hash_password(new_password)
    save_config(config)
    return True, "Jelszó sikeresen megváltoztatva"

# Konfiguráció betöltése és mentése
def load_config():
    try:
        with open(QUIZ_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"active_quiz": "magyar_foldrajz", "quiz_settings": {}}

def save_config(config):
    with open(QUIZ_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

# Inicializálás
def init_data():
    if not os.path.exists(QUIZ_RESULTS_DIR):
        os.makedirs(QUIZ_RESULTS_DIR)
    
    if not os.path.exists(QUIZZES_DIR):
        os.makedirs(QUIZZES_DIR)
        create_sample_quizzes()
    
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    
    config = load_config()
    
    if "teacher_password_hash" not in config:
        config["teacher_password_hash"] = hash_password("tanar123")
        save_config(config)
    
    if not os.path.exists(STUDENTS_FILE):
        default_students = {
            "classes": {},
            "students": {}
        }
        with open(STUDENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_students, f, indent=2, ensure_ascii=False)

def create_sample_quizzes():
    magyar_foldrajz = [
        {
            "question": "Mi a fővárosa Magyarországnak?",
            "type": "single",
            "options": ["Budapest", "Bécs", "Prága", "Varsó"],
            "answer": "Budapest",
            "points": 1
        }
    ]
    
    with open(os.path.join(QUIZZES_DIR, "magyar_foldrajz.json"), 'w', encoding='utf-8') as f:
        json.dump(magyar_foldrajz, f, indent=2, ensure_ascii=False)

# Diák adatok kezelése
def load_students():
    try:
        with open(STUDENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"classes": {}, "students": {}}

def save_students(students_data):
    with open(STUDENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(students_data, f, indent=2, ensure_ascii=False)

def get_classes():
    students_data = load_students()
    return list(students_data.get("classes", {}).keys())

def get_students_in_class(class_name):
    students_data = load_students()
    return students_data.get("classes", {}).get(class_name, {})

def add_student(class_name, student_name, email, password):
    students_data = load_students()
    
    if class_name not in students_data["classes"]:
        students_data["classes"][class_name] = {}
    
    student_id = email.lower()
    students_data["classes"][class_name][student_id] = {
        "name": student_name,
        "email": email,
        "password_hash": hash_password(password)
    }
    
    students_data["students"][student_id] = {
        "name": student_name,
        "email": email,
        "class": class_name
    }
    
    save_students(students_data)

def delete_student(class_name, student_id):
    students_data = load_students()
    
    if class_name in students_data["classes"] and student_id in students_data["classes"][class_name]:
        del students_data["classes"][class_name][student_id]
        
        if student_id in students_data["students"]:
            del students_data["students"][student_id]
        
        save_students(students_data)
        return True
    return False

def authenticate_student(email, password):
    students_data = load_students()
    student_id = email.lower()
    
    if student_id in students_data["students"]:
        student_info = students_data["students"][student_id]
        class_name = student_info["class"]
        
        if class_name in students_data["classes"] and student_id in students_data["classes"][class_name]:
            stored_hash = students_data["classes"][class_name][student_id]["password_hash"]
            if verify_password(password, stored_hash):
                return {
                    "name": student_info["name"],
                    "email": student_info["email"],
                    "class": class_name
                }
    return None

# Képkezelés funkciók
def save_image(uploaded_file, quiz_id, question_index):
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        filename = f"{quiz_id}_q{question_index}{file_extension}"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return filename
    return None

def get_image_path(filename):
    if filename and os.path.exists(os.path.join(IMAGES_DIR, filename)):
        return os.path.join(IMAGES_DIR, filename)
    return None

def display_image(filename, caption=None, width=None):
    if filename:
        image_path = get_image_path(filename)
        if image_path and os.path.exists(image_path):
            try:
                st.image(image_path, caption=caption, width=width)
            except Exception as e:
                st.error(f"Hiba a kép megjelenítésekor: {e}")
        else:
            st.warning(f"A kép fájl nem található: {filename}")
    else:
        st.warning("Nincs kép fájlnév megadva")

def delete_image(filename):
    if filename:
        image_path = get_image_path(filename)
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

# Quiz adatok betöltése és mentése
def load_quiz(quiz_id):
    try:
        with open(os.path.join(QUIZZES_DIR, f"{quiz_id}.json"), 'r', encoding='utf-8') as f:
            quiz_data = json.load(f)
            for question in quiz_data:
                if question["type"] == "single" and isinstance(question["answer"], list):
                    if question["answer"]:
                        question["answer"] = question["answer"][0]
                    else:
                        question["answer"] = ""
            return quiz_data
    except:
        return []

def save_quiz(quiz_id, quiz_data):
    with open(os.path.join(QUIZZES_DIR, f"{quiz_id}.json"), 'w', encoding='utf-8') as f:
        json.dump(quiz_data, f, indent=2, ensure_ascii=False)

def get_available_quizzes(for_student=False):
    quizzes = {}
    if os.path.exists(QUIZZES_DIR):
        for file in os.listdir(QUIZZES_DIR):
            if file.endswith('.json'):
                quiz_id = file[:-5]
                try:
                    quiz_data = load_quiz(quiz_id)
                    if quiz_data and len(quiz_data) > 0:
                        # Diákoknak csak a látható quizeket jelenítjük meg
                        if for_student:
                            config = load_config()
                            quiz_settings = config.get("quiz_settings", {}).get(quiz_id, {})
                            if not quiz_settings.get("visible_to_students", False):
                                continue
                        
                        quizzes[quiz_id] = {
                            "name": quiz_data[0].get("quiz_name", quiz_id.replace("_", " ").title()),
                            "question_count": len(quiz_data)
                        }
                except:
                    continue
    return quizzes

# Eredmények kezelése quiz-enként
def get_results_file(quiz_id):
    return os.path.join(QUIZ_RESULTS_DIR, f"{quiz_id}_results.csv")

def load_results(quiz_id):
    results_file = get_results_file(quiz_id)
    if os.path.exists(results_file):
        return pd.read_csv(results_file)
    else:
        return pd.DataFrame(columns=[
            "student_name", "student_email", "score", "total_questions", "percentage", 
            "timestamp", "answers", "class", "max_points", "grade", "quiz_id"
        ])

def save_results(quiz_id, results_df):
    results_file = get_results_file(quiz_id)
    results_df.to_csv(results_file, index=False)

# Osztályzat kalkulátor függvény
def calculate_grade(percentage):
    if percentage < 40:
        return 1
    elif 40 <= percentage < 55:
        return 2
    elif 55 <= percentage < 70:
        return 3
    elif 70 <= percentage < 85:
        return 4
    else:
        return 5

def normalize_text(text):
    if text is None:
        return ""
    return re.sub(r'\s+', ' ', str(text).strip().lower())

def parse_number(text):
    """
    Szöveges bemenetet számmá alakít, támogatja a tört formátumot is.
    Pl.: "29/5" -> 5.8, "13/10" -> 1.3, "18/5" -> 3.6
    """
    if text is None:
        return None
    
    text = normalize_text(text)
    
    if '/' in text:
        parts = text.split('/')
        if len(parts) == 2:
            try:
                numerator = float(parts[0])
                denominator = float(parts[1])
                if denominator != 0:
                    return numerator / denominator
            except (ValueError, ZeroDivisionError):
                pass
    
    try:
        return float(text.replace(',', '.'))
    except ValueError:
        return None

def evaluate_text_answer(student_answer, correct_answers, match_type="exact"):
    student_normalized = normalize_text(student_answer)
    
    if match_type == "number":
        student_num = parse_number(student_answer)
        if student_num is None:
            return False
        
        correct_nums = []
        for ca in correct_answers:
            num = parse_number(ca)
            if num is not None:
                correct_nums.append(num)
        
        if not correct_nums:
            return False
        
        return any(abs(student_num - correct_num) < 0.001 for correct_num in correct_nums)
    
    elif match_type == "contains":
        correct_normalized = [normalize_text(ca) for ca in correct_answers]
        return any(correct in student_normalized for correct in correct_normalized)
    
    else:
        correct_normalized = [normalize_text(ca) for ca in correct_answers]
        return student_normalized in correct_normalized

# Kérdéstípusok címkéi
type_labels = {
    "single": "Egyszeres választós",
    "multiple": "Többszörös választós", 
    "text": "Szöveges válasz"
}

def get_randomized_quiz(quiz_data):
    randomized_quiz = quiz_data.copy()
    random.shuffle(randomized_quiz)
    
    for question in randomized_quiz:
        if question["type"] in ["single", "multiple"]:
            options = question["options"].copy()
            random.shuffle(options)
            question["options"] = options
    
    return randomized_quiz

def get_random_subset_quiz(quiz_data, num_questions):
    if num_questions >= len(quiz_data):
        return get_randomized_quiz(quiz_data)
    
    selected_questions = random.sample(quiz_data, num_questions)
    return get_randomized_quiz(selected_questions)

def calculate_score(user_answer, correct_answer, question_type, points, match_type="exact"):
    if question_type == "single":
        if isinstance(correct_answer, list):
            if correct_answer:
                correct_answer = correct_answer[0]
            else:
                correct_answer = ""
        return points if user_answer == correct_answer else 0
    elif question_type == "multiple":
        user_set = set(user_answer)
        correct_set = set(correct_answer)
        correct_selected = len(user_set & correct_set)
        incorrect_selected = len(user_set - correct_set)
        
        partial_score = max(0, correct_selected - incorrect_selected) * (points / len(correct_set))
        return round(partial_score, 2)
    else:
        is_correct = evaluate_text_answer(user_answer, correct_answer, match_type)
        return points if is_correct else 0

# Diák eredményeinek részletes megjelenítése
def display_student_result(student_result, quiz_data):
    """Egy diák eredményének részletes megjelenítése"""
    
    st.subheader(f"📝 {student_result['student_name']} részletes eredménye")
    
    # Alapadatok
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Név", student_result['student_name'])
    with col2:
        st.metric("Email", student_result.get('student_email', 'N/A'))
    with col3:
        st.metric("Pontszám", f"{student_result['score']}/{student_result['max_points']}")
    with col4:
        st.metric("Százalék", f"{student_result['percentage']}%")
    
    # Osztályzat
    grade = student_result['grade']
    grade_colors = {1: "red", 2: "orange", 3: "yellow", 4: "lightgreen", 5: "green"}
    st.markdown(f"<h3 style='color: {grade_colors[grade]}; text-align: center;'>Osztályzat: {grade}</h3>", 
                unsafe_allow_html=True)
    
    # Időpont
    st.write(f"**Kitöltés időpontja:** {student_result['timestamp']}")
    
    # Részletes válaszok
    st.subheader("📋 Kérdések és válaszok")
    
    try:
        answers = json.loads(student_result['answers'])
        
        for i, answer in enumerate(answers, 1):
            # Expanderek helyett egyszerű szakaszokat használunk
            st.markdown(f"**{i}. kérdés:** {answer.get('question', '')}")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Állapot ikon
                status = "✅" if answer.get("is_correct", False) else "⚠️" if answer.get("earned_points", 0) > 0 else "❌"
                type_label = type_labels.get(answer.get("type", ""), answer.get("type", ""))
                st.write(f"{status} **{answer.get('question', '')}** (*{type_label}*)")
                
                # Kép megjelenítése, ha van
                if "image" in answer and answer["image"]:
                    display_image(answer["image"], width=300)
                
                # Diák válasza
                student_answer = answer.get('student_answer', '')
                if answer.get("type") == "text":
                    st.write(f"**Te válaszod:** {student_answer}")
                else:
                    if isinstance(student_answer, list):
                        st.write(f"**Te válaszod:** {', '.join(student_answer)}")
                    else:
                        st.write(f"**Te válaszod:** {student_answer}")
                
                # Helyes válasz
                correct_answer = answer.get('correct_answer', '')
                if isinstance(correct_answer, list):
                    st.write(f"**Helyes válasz(ok):** {', '.join(correct_answer)}")
                else:
                    st.write(f"**Helyes válasz:** {correct_answer}")
                
                # Értékelés típusa szöveges kérdésnél
                if answer.get("type") == "text" and "match_type" in answer:
                    match_type_labels = {
                        "exact": "Pontos egyezés",
                        "contains": "Tartalmazás",
                        "number": "Numerikus érték"
                    }
                    st.write(f"**Értékelés típusa:** {match_type_labels.get(answer['match_type'], answer['match_type'])}")
            
            with col2:
                earned = answer.get('earned_points', 0)
                max_points = answer.get('max_points', 0)
                st.write(f"**{earned}/{max_points} pont**")
                
                if earned == max_points:
                    st.success("Teljes pontszám!")
                elif earned > 0:
                    st.warning("Részleges pontszám")
                else:
                    st.error("0 pont")
            
            st.markdown("---")
    
    except Exception as e:
        st.error(f"Hiba a válaszok betöltése során: {e}")

init_data()