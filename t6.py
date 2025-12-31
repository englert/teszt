import streamlit as st
import pandas as pd
from common import *

def teacher_students_management():
    st.header("👥 Diákok és osztályok kezelése")
    
    students_data = load_students()
    classes = students_data.get("classes", {})
    
    col1, col2 = st.columns([3, 1])
    with col1:
        new_class_name = st.text_input("Új osztály neve", placeholder="pl. 9.A")
    with col2:
        if st.button("➕ Osztály hozzáadása"):
            if new_class_name and new_class_name not in classes:
                classes[new_class_name] = {}
                students_data["classes"] = classes
                save_students(students_data)
                st.success(f"'{new_class_name}' osztály létrehozva!")
                st.rerun()
            else:
                st.error("Az osztály név nem lehet üres vagy már létezik!")
    
    if classes:
        # Osztály kiválasztása rádiógombokkal
        st.subheader("Válassz osztályt:")
        selected_class = st.radio(
            "Osztályok:",
            options=list(classes.keys()),
            key="class_selector_radio"
        )
        
        st.subheader(f"Diákok kezelése - {selected_class}")
        
        with st.expander("➕ Új diák hozzáadása", expanded=True):
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                new_student_name = st.text_input("Diák neve", key="new_student_name")
            with col2:
                new_student_email = st.text_input("Email cím", key="new_student_email")
            with col3:
                new_student_password = st.text_input("Jelszó", type="password", key="new_student_password")
            
            if st.button("💾 Diák hozzáadása"):
                if new_student_name and new_student_email and new_student_password:
                    email_exists = False
                    for class_name, class_students in classes.items():
                        for student_id, student_info in class_students.items():
                            if student_info["email"].lower() == new_student_email.lower():
                                email_exists = True
                                break
                        if email_exists:
                            break
                    
                    if email_exists:
                        st.error("Ez az email cím már használatban van!")
                    else:
                        add_student(selected_class, new_student_name, new_student_email, new_student_password)
                        st.success(f"'{new_student_name}' hozzáadva a(z) '{selected_class}' osztályhoz!")
                        st.rerun()
                else:
                    st.error("Minden mezőt ki kell tölteni!")
        
        st.subheader(f"Diákok listája - {selected_class}")
        class_students = classes.get(selected_class, {})
        
        if class_students:
            for student_id, student_info in class_students.items():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**Név:** {student_info['name']}")
                with col2:
                    st.write(f"**Email:** {student_info['email']}")
                with col3:
                    if st.button("🗑️ Törlés", key=f"delete_{student_id}"):
                        if delete_student(selected_class, student_id):
                            st.success(f"'{student_info['name']}' törölve!")
                            st.rerun()
        else:
            st.info("Ez az osztály még nem tartalmaz diákokat.")
    else:
        st.info("Még nincsenek osztályok. Hozz létre egy újat!")

def teacher_quiz_management():
    st.header("📚 Quiz Választás")
    
    available_quizzes = get_available_quizzes()
    
    if not available_quizzes:
        st.info("Nincsenek elérhető quizek. Hozz létre egy újat!")
        quiz_options = []
    else:
        quiz_options = {qid: f"{data['name']} ({data['question_count']} kérdés)" 
                       for qid, data in available_quizzes.items()}
    


    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
    
    
    with col1:
        if 'teacher_selected_quiz' not in st.session_state:
            st.session_state.teacher_selected_quiz = list(quiz_options.keys())[0] if quiz_options else ""
        
        selected_quiz_id = st.selectbox(
            "Válassz quizzet:",
            options=list(quiz_options.keys()) if quiz_options else [""],
            format_func=lambda x: quiz_options.get(x, "Új quiz létrehozása"),
            key="teacher_quiz_selector",
            index=list(quiz_options.keys()).index(st.session_state.teacher_selected_quiz) 
            if quiz_options and st.session_state.teacher_selected_quiz in quiz_options else 0
        )
        
        if selected_quiz_id != st.session_state.teacher_selected_quiz:
            st.session_state.teacher_selected_quiz = selected_quiz_id
            st.rerun()
    
    with col2:
        new_quiz_name = st.text_input("Új quiz neve", placeholder="Új quiz neve", key="new_quiz_name")
        if st.button("➕ Új quiz") and new_quiz_name:
            new_quiz_id = new_quiz_name.lower().replace(" ", "_")
            new_quiz_data = [{
                "question": "Első kérdés",
                "type": "single",
                "options": ["1. válasz", "2. válasz", "3. válasz", "4. válasz"],
                "answer": "1. válasz",
                "points": 1
            }]
            save_quiz(new_quiz_id, new_quiz_data)
            st.success(f"'{new_quiz_name}' quiz létrehozva!")
            st.session_state.teacher_selected_quiz = new_quiz_id
            st.rerun()

    with col4:
        css  = """
            .st-key-ai {
                background-color: #1d1d1d;
                border-radius: 10px;
                padding: 10px;
            }

        """
        st.html(f"<style>{css}</style>")
        with st.container(key="ai"):
            st.html("""
            <h1>Feladat generálása AI segítségével</h1>
            <style></style>
            """)
            ai_task_name = st.text_input("Feladatsor neve", placeholder="Feladatsor neve", key="ai_task_name")
            ai_topic_name = st.text_input("Téma neve", placeholder="Téma neve", key="ai_topic_name")
            ai_teacher_desc = st.text_area("Egyéb paraméterek", placeholder="Egyéb paraméterek", key="ai_teacher_desc")
            ai_num_of_task = st.text_input("Feladatok száma", placeholder="Feladatok száma", key="ai_num_of_task")
            if st.button("AI álltal generált feladatsor") and ai_task_name and ai_num_of_task and ai_topic_name:
                
                conf = load_config()
                gen_task(api_key=conf["api_key"], task_name=ai_task_name, task_topic=ai_topic_name, num_of_task=ai_num_of_task, ai_teacher_desc=ai_teacher_desc)
    
    
    if not st.session_state.teacher_selected_quiz:
        st.info("Válassz ki egy quizt a listából, vagy hozz létre egy újat.")
        return
    
    selected_quiz_id = st.session_state.teacher_selected_quiz
    
    quiz_data = load_quiz(selected_quiz_id)
    if not quiz_data:
        st.error("A kiválasztott quiz nem található.")
        return
    
    total_questions = len(quiz_data)
    
    st.header("📋 Quiz Beállítások")
    
    config = load_config()
    quiz_settings = config.get("quiz_settings", {}).get(selected_quiz_id, {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        show_correct_answers = st.checkbox(
            "Helyes válaszok megjelenítése a diákoknak", 
            value=quiz_settings.get("show_correct_answers", True)
        )
    
    with col2:
        allow_retake = st.checkbox(
            "Újrakezdés engedélyezése", 
            value=quiz_settings.get("allow_retake", True)
        )
    
    with col3:
        shuffle_questions = st.checkbox(
            "Kérdések összekeverése", 
            value=quiz_settings.get("shuffle_questions", True)
        )
    
    # Láthatóság beállítása a diákok számára
    visible_to_students = st.checkbox(
        "Látható a diákok számára",
        value=quiz_settings.get("visible_to_students", False),
        help="Ha be van jelölve, a diákok láthatják és kitölthetik ezt a quizt."
    )
    
    questions_to_show = st.number_input(
        "Megjelenítendő kérdések száma",
        min_value=0,
        max_value=total_questions,
        value=quiz_settings.get("questions_to_show", 0),
        help=f"Ha 0, akkor az összes {total_questions} kérdés megjelenik."
    )
    
    if questions_to_show > 0:
        st.info(f"⚠️ A diákok {questions_to_show} véletlenszerűen kiválasztott kérdést kapnak az összes {total_questions} kérdésből.")
    
    active_quiz = st.checkbox(
        "Aktív quiz", 
        value=config.get("active_quiz") == selected_quiz_id
    )
    
    if st.button("Beállítások mentése"):
        quiz_settings = {
            "show_correct_answers": show_correct_answers,
            "allow_retake": allow_retake,
            "shuffle_questions": shuffle_questions,
            "questions_to_show": questions_to_show,
            "visible_to_students": visible_to_students
        }
        
        if "quiz_settings" not in config:
            config["quiz_settings"] = {}
        
        config["quiz_settings"][selected_quiz_id] = quiz_settings
        
        if active_quiz:
            config["active_quiz"] = selected_quiz_id
        
        save_config(config)
        st.success("Beállítások sikeresen mentve!")
    
    st.header("✏️ Quiz Szerkesztése")
    
    st.info(f"Jelenleg {total_questions} kérdés található a quizben.")
    
    type_display_names = {
        "single": "Egyszeres választós",
        "multiple": "Többszörös választós",
        "text": "Szöveges válasz"
    }
    
    for i, question in enumerate(quiz_data):
        with st.expander(f"Kérdés {i+1}: {question['question'][:50]}...", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                new_question = st.text_area(f"Kérdés {i+1}", value=question["question"], key=f"q_{selected_quiz_id}_{i}_text")
                
                st.subheader("Kép a kérdéshez")
                
                if "image" in question and question["image"]:
                    st.write("Jelenlegi kép:")
                    display_image(question["image"], width=300)
                    
                    if st.button("🗑️ Kép törlése", key=f"del_img_{selected_quiz_id}_{i}"):
                        delete_image(question["image"])
                        question.pop("image", None)
                        save_quiz(selected_quiz_id, quiz_data)
                        st.success("Kép törölve!")
                        st.rerun()
                
                uploaded_file = st.file_uploader(
                    f"Kép feltöltése a kérdéshez {i+1}", 
                    type=['png', 'jpg', 'jpeg', 'gif'],
                    key=f"upload_{selected_quiz_id}_{i}"
                )
                
                if uploaded_file is not None:
                    try:
                        image = Image.open(uploaded_file)
                        st.image(image, caption="Feltöltött kép előnézete", width=300)
                    except Exception as e:
                        st.error(f"Hiba a kép előnézetének megjelenítésekor: {e}")
                    
                    if st.button("💾 Kép mentése", key=f"save_img_{selected_quiz_id}_{i}"):
                        filename = save_image(uploaded_file, selected_quiz_id, i)
                        if filename:
                            question["image"] = filename
                            save_quiz(selected_quiz_id, quiz_data)
                            st.success("Kép sikeresen mentve!")
                            st.rerun()
                
                st.write("**Kérdés típusa:**")
                question_type = st.radio(
                    f"Kérdés típusa {i+1}",
                    options=["single", "multiple", "text"],
                    format_func=lambda x: type_display_names[x],
                    index=["single", "multiple", "text"].index(question["type"]),
                    key=f"q_{selected_quiz_id}_{i}_type",
                    horizontal=True
                )
                
                points = st.number_input(f"Pontérték {i+1}", min_value=1, value=question["points"], key=f"q_{selected_quiz_id}_{i}_points")
                
                if question_type in ["single", "multiple"]:
                    st.write("Válaszlehetőségek:")
                    options = question["options"]
                    for j, option in enumerate(options):
                        options[j] = st.text_input(f"Opció {j+1}", value=option, key=f"q_{selected_quiz_id}_{i}_opt_{j}")
                    
                    if st.button(f"➕ Opció hozzáadása", key=f"add_opt_{selected_quiz_id}_{i}"):
                        options.append("Új opció")
                        st.rerun()
                    
                    if question_type == "single":
                        current_answer = question["answer"]
                        if isinstance(current_answer, list):
                            if current_answer:
                                current_answer = current_answer[0]
                            else:
                                current_answer = options[0] if options else ""
                        
                        correct_answer = st.radio(
                            f"Helyes válasz {i+1}",
                            options=options,
                            index=options.index(current_answer) if current_answer in options else 0,
                            key=f"q_{selected_quiz_id}_{i}_correct"
                        )
                    else:
                        current_answers = question["answer"]
                        if not isinstance(current_answers, list):
                            current_answers = [current_answers] if current_answers else []
                        
                        correct_answers = st.multiselect(
                            f"Helyes válaszok {i+1}",
                            options=options,
                            default=current_answers,
                            key=f"q_{selected_quiz_id}_{i}_correct_multi"
                        )
                else:
                    st.write("Helyes válasz(ok) - több is lehet, enterrel elválasztva:")
                    current_answers = question["answer"]
                    if not isinstance(current_answers, list):
                        current_answers = [current_answers] if current_answers else []
                    
                    correct_answers_text = st.text_area(
                        f"Helyes válaszok {i+1}",
                        value="\n".join(current_answers),
                        key=f"q_{selected_quiz_id}_{i}_correct_text"
                    )
                    
                    match_type = st.radio(
                        f"Értékelés típusa {i+1}",
                        options=["exact", "contains", "number"],
                        index=["exact", "contains", "number"].index(question.get("match_type", "exact")),
                        key=f"q_{selected_quiz_id}_{i}_match",
                        horizontal=True
                    )
            
            with col2:
                if st.button("🗑️ Kérdés törlése", key=f"del_{selected_quiz_id}_{i}"):
                    if "image" in question and question["image"]:
                        delete_image(question["image"])
                    quiz_data.pop(i)
                    save_quiz(selected_quiz_id, quiz_data)
                    st.success("Kérdés törölve!")
                    st.rerun()
            
            if st.button("💾 Módosítások mentése", key=f"save_{selected_quiz_id}_{i}"):
                quiz_data[i]["question"] = new_question
                quiz_data[i]["type"] = question_type
                quiz_data[i]["points"] = points
                
                if question_type in ["single", "multiple"]:
                    quiz_data[i]["options"] = options
                    if question_type == "single":
                        quiz_data[i]["answer"] = correct_answer
                    else:
                        quiz_data[i]["answer"] = correct_answers
                else:
                    quiz_data[i]["answer"] = [ans.strip() for ans in correct_answers_text.split("\n") if ans.strip()]
                    quiz_data[i]["match_type"] = match_type
                
                save_quiz(selected_quiz_id, quiz_data)
                st.success("Kérdés mentve!")
    
    if st.button("➕ Új kérdés hozzáadása", key=f"add_question_{selected_quiz_id}"):
        new_question = {
            "question": "Új kérdés",
            "type": "single",
            "options": ["1. válasz", "2. válasz", "3. válasz", "4. válasz"],
            "answer": "1. válasz",
            "points": 1
        }
        quiz_data.append(new_question)
        save_quiz(selected_quiz_id, quiz_data)
        st.success("Új kérdés hozzáadva!")
        st.rerun()

def teacher_results_management():
    st.header("📊 Quiz Eredmények")
    
    if 'teacher_selected_quiz' not in st.session_state:
        st.info("Először válassz ki egy quizzet a 'Quiz Szerkesztése' menüpontban!")
        return
    
    selected_quiz_id = st.session_state.teacher_selected_quiz
    quiz_data = load_quiz(selected_quiz_id)
    
    try:
        df = load_results(selected_quiz_id)
        if df.empty:
            st.info("Még nincsenek eredmények ehhez a quizhez.")
        else:
            df['grade'] = pd.to_numeric(df['grade'], errors='coerce')
            df = df.dropna(subset=['grade'])
            df['grade'] = df['grade'].astype(int)
            
            st.sidebar.header("Szűrők")
            
            # Osztály kiválasztása rádiógombokkal
            st.sidebar.subheader("Osztály")
            class_options = ["Összes"] + list(df['class'].unique())
            selected_class = st.sidebar.radio(
                "Válassz osztályt:",
                options=class_options,
                key="results_class_radio"
            )
            
            selected_grade = st.sidebar.selectbox("Osztályzat", ["Összes", "1", "2", "3", "4", "5"])
            date_range = st.sidebar.date_input("Dátum tartomány", [])
            
            filtered_df = df.copy()
            if selected_class != "Összes":
                filtered_df = filtered_df[filtered_df['class'] == selected_class]
            
            if selected_grade != "Összes":
                filtered_df = filtered_df[filtered_df['grade'] == int(selected_grade)]
            
            if len(date_range) == 2:
                filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'])
                filtered_df = filtered_df[
                    (filtered_df['timestamp'].dt.date >= date_range[0]) & 
                    (filtered_df['timestamp'].dt.date <= date_range[1])
                ]
            
            st.subheader("Áttekintés")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Összes kitöltés", len(filtered_df))
            with col2:
                avg_score = filtered_df['percentage'].mean()
                st.metric("Átlagos pontszám", f"{avg_score:.1f}%")
            with col3:
                best_score = filtered_df['percentage'].max()
                st.metric("Legjobb eredmény", f"{best_score:.1f}%")
            with col4:
                completion_count = len(filtered_df['student_name'].unique())
                st.metric("Különböző diákok", completion_count)
            with col5:
                avg_grade = filtered_df['grade'].mean()
                st.metric("Átlagos osztályzat", f"{avg_grade:.1f}")
            
            # Diák kiválasztása részletes eredményhez - TÁBLÁZATOS MEGJELENÍTÉS
            st.subheader("🔍 Diákok eredményei")
            
            if not filtered_df.empty:
                # Reset index for stable row identification
                filtered_df_display = filtered_df.reset_index(drop=True)
                
                # Táblázat fejléce
                col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
                col1.write("**Név**")
                col2.write("**Email**")
                col3.write("**Osztály**")
                col4.write("**Pontszám**")
                col5.write("**Százalék**")
                col6.write("**Osztályzat**")
                col7.write("**Dátum**")
                
                # Minden sor megjelenítése
                for index, row in filtered_df_display.iterrows():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1, 1, 1, 1, 1])
                    
                    col1.write(row['student_name'])
                    col2.write(row['student_email'])
                    col3.write(row['class'])
                    col4.write(f"{row['score']}/{row['max_points']}")
                    col5.write(f"{row['percentage']}%")
                    
                    # Osztályzat színes megjelenítése
                    grade = row['grade']
                    grade_colors = {1: "red", 2: "orange", 3: "yellow", 4: "lightgreen", 5: "green"}
                    col6.markdown(f"<span style='color: {grade_colors[grade]}; font-weight: bold;'>{grade}</span>", 
                                 unsafe_allow_html=True)
                    
                    col7.write(row['timestamp'])
                
                # Vonal a táblázat alatt
                st.markdown("---")
                
                # Diák kiválasztása részletes eredményhez
                st.subheader("Részletes eredmény megtekintése")
                
                # Diák kiválasztása
                student_options = [f"{row['student_name']} ({row['class']}) - {row['timestamp']}" 
                                  for _, row in filtered_df.iterrows()]
                
                if student_options:
                    selected_student = st.selectbox(
                        "Válassz egy diákot a részletes eredmény megtekintéséhez:",
                        options=student_options,
                        key="student_detail_selector"
                    )
                    
                    if st.button("📋 Részletes eredmény megjelenítése"):
                        # Kiválasztott diák adatainak lekérése
                        selected_index = student_options.index(selected_student)
                        selected_row = filtered_df.iloc[selected_index]
                        
                        # Diák eredményének megjelenítése
                        display_student_result(selected_row.to_dict(), quiz_data)
                else:
                    st.info("Nincs megjeleníthető diák a kiválasztott szűrőkkel.")
            
            st.subheader("Eredmények Exportálása")
            
            # CSV letöltés a kért oszlopokkal
            export_df = filtered_df[['student_name', 'student_email', 'class', 'score', 'max_points', 'percentage', 'grade', 'timestamp']].copy()
            export_df = export_df.rename(columns={
                'student_name': 'Név',
                'student_email': 'Email',
                'class': 'Osztály',
                'score': 'Pontszám',
                'max_points': 'Maximális pont',
                'percentage': 'Százalék',
                'grade': 'Érdemjegy',
                'timestamp': 'Dátum'
            })
            
            csv = export_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Eredmények letöltése CSV-ként",
                data=csv,
                file_name=f"{selected_quiz_id}_eredmenyek_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                help="Letölti az eredményeket CSV fájlként a következő oszlopokkal: Név, Email, Osztály, Pontszám, Maximális pont, Százalék, Érdemjegy, Dátum"
            )
    except Exception as e:
        st.error(f"Hiba az eredmények betöltése során: {e}")

def teacher_settings():
    st.header("⚙️ Tanári Beállítások")
    
    st.subheader("Jelszó megváltoztatása")
    
    old_password = st.text_input("Régi jelszó", type="password")
    new_password = st.text_input("Új jelszó", type="password")
    confirm_password = st.text_input("Új jelszó megerősítése", type="password")
    
    if st.button("Jelszó megváltoztatása"):
        if not old_password or not new_password or not confirm_password:
            st.error("Minden mezőt ki kell tölteni!")
        elif new_password != confirm_password:
            st.error("Az új jelszavak nem egyeznek!")
        else:
            success, message = change_teacher_password(old_password, new_password)
            if success:
                st.success(message)
            else:
                st.error(message)

    config = load_config()
    st.header("AI Beállításai")
    st.text("Hogyan szerezzek api kulcsot?")
    if st.checkbox(label="API kulcs szerkesztése"):
        if st.button("Fejlesztői jelszó", type="tertiary"):
            st.toast(icon="💡", body="A fejlesztői jelszó megváltoztatható itt:```~/quiz_config.json```>```dev_passw```", duration='long')
        check_container = st.empty()
        
        dev_passw = check_container.text_input("Jelszó", type="password")
        if st.checkbox("Szerkesztés engedélyezése"):
            if simple_hash(dev_passw) == config["dev_passw"]:
                st.toast(icon="✅", body="#### ```Sikeres azonosítás```", duration=2)
                check_container.empty()
                api_key = st.text_input("Google API Key", value="..."+config["api_key"][-4:])
                st.text("Hogyan szerezzek api kulcsot?: "); st.link_button("Google API kulcs létrehozása", "https://aistudio.google.com/api-keys")
                if st.button("api kulcs mentése"):
                    config["api_key"] = api_key
                    save_config(config)
                if st.button("API kulcs törlése"):
                    config["api_key"] = "API kulcs"
                    save_config(config)
                    st.warning("API kulcs törölve.")
            else:
                st.toast(icon="❌", body="##### ```Sikertelen azonosítás```", duration=2)

       
    st.html("<hr>")
    if st.checkbox(label="Részletes prompt"):
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 0.5, 1, 1, 1, 1, 1])
    
        with col1:
            resz1 = st.text_area("Részletes promt 1. része", value=config["prompt"]["resz1"])
            if st.button("Első rész mentése"):
                config["prompt"]["resz1"] = resz1
                save_config(config)
                st.success("A mentés sikeres")
        with col2:
            st.space()
            st.subheader("témakör.")
        with col3:
            resz2 = st.text_area("Részletes promt 2. része", value=config["prompt"]["resz2"])
            if st.button("Második rész mentése"):
                config["prompt"]["resz2"] = resz2
                save_config(config)
                st.success("A mentés sikeres")
        with col4:
            st.space()
            st.subheader("Feladatok száma.")
        with col5:
            resz3 = st.text_area("Részletes promt 3. része", value=config["prompt"]["resz3"], height=200)
            if st.button("Harmadik rész mentése"):
                config["prompt"]["resz3"] = resz3
                save_config(config)
                st.success("A mentés sikeres")
        with col6:
            st.space()
            st.subheader("Tanár szövege.")
        with col7:
            resz4 = st.text_area("Részletes promt 4. része", value=config["prompt"]["resz4"], height=300)
            if st.button("Negyedik rész mentése"):
                config["prompt"]["resz4"] = resz4
                save_config(config)
                st.success("A mentés sikeres")
    else:
        prompt = st.text_area("Egyszerű prompt", value=config["prompt"]["resz4"])
        if st.button("Mentés"):
            config["prompt"]["resz4"] = prompt
            save_config(config)
            st.success("A mentés sikeres")
    




def teacher_interface():
    st.title("👨‍🏫 Tanári Felület")
    
    if 'teacher_logged_in' not in st.session_state:
        st.session_state.teacher_logged_in = False
    
    if not st.session_state.teacher_logged_in:
        password = st.text_input("Tanári jelszó", type="password")
        if st.button("Bejelentkezés"):
            if verify_teacher_password(password):
                st.session_state.teacher_logged_in = True
                if 'teacher_selected_quiz' not in st.session_state:
                    st.session_state.teacher_selected_quiz = None
                st.success("Sikeres bejelentkezés!")
                st.rerun()
            else:
                st.error("Hibás jelszó!")
        return
    
    st.sidebar.title("Tanári Navigáció")
    
    if 'teacher_menu' not in st.session_state:
        st.session_state.teacher_menu = "Diákok és osztályok kezelése"
    
    menu_options = [
        "Diákok és osztályok kezelése",
        "Quiz Szerkesztése", 
        "Quiz Eredmények",
        "Beállítások"
    ]
    
    selected_menu = st.sidebar.radio(
        "Válassz menüpontot:",
        menu_options,
        index=menu_options.index(st.session_state.teacher_menu)
    )
    
    if selected_menu != st.session_state.teacher_menu:
        st.session_state.teacher_menu = selected_menu
        st.rerun()
    
    if st.sidebar.button("Kijelentkezés"):
        st.session_state.teacher_logged_in = False
        st.session_state.teacher_menu = "Diákok és osztályok kezelése"
        st.rerun()
    
    if selected_menu == "Diákok és osztályok kezelése":
        teacher_students_management()
    elif selected_menu == "Quiz Szerkesztése":
        teacher_quiz_management()
    elif selected_menu == "Quiz Eredmények":
        teacher_results_management()
    elif selected_menu == "Beállítások":
        teacher_settings()

def main():
    setup_page_config()
    teacher_interface()

if __name__ == "__main__":
    main()