import logging
import mysql.connector
from mysql.connector import Error
from data.config import mysqlHost, mysqlUser, mysqlPassword, mysqlDatabase

logger = logging.getLogger(__name__)

def getConnection():
    try:
        conn = mysql.connector.connect(
            host=mysqlHost,
            user=mysqlUser,
            password=mysqlPassword,
            database=mysqlDatabase
        )
        return conn
    except Error as error:
        logger.error("DB connection error: {}".format(error))
        return None

def initDb():
    conn = getConnection()
    if conn is None:
        return
    try:
        with conn.cursor() as cursor:
            # Таблица пользователей
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    userId BIGINT NOT NULL,
                    userName VARCHAR(255) NOT NULL,
                    firstName VARCHAR(255) DEFAULT NULL,
                    lastName VARCHAR(255) DEFAULT NULL,
                    middleName VARCHAR(255) DEFAULT NULL,
                    phone VARCHAR(20) DEFAULT NULL,
                    role VARCHAR(10) NOT NULL DEFAULT 'user',
                    joinDate DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    isBlocked TINYINT(1) NOT NULL DEFAULT '0',
                    UNIQUE KEY unique_user (userId)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )

            # Таблица категорий тестов
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active TINYINT(1) NOT NULL DEFAULT '1'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )

            # Таблица тестов
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    is_active TINYINT(1) NOT NULL DEFAULT '1',
                    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )

            # Таблица вопросов
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_id INT NOT NULL,
                    question_text TEXT NOT NULL,
                    image_path VARCHAR(500) DEFAULT NULL,
                    question_order INT NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )

            # Таблица ответов
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    question_id INT NOT NULL,
                    answer_text TEXT NOT NULL,
                    is_correct TINYINT(1) NOT NULL DEFAULT '0',
                    answer_order INT NOT NULL,
                    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )

            # Таблица результатов тестов
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS test_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    test_id INT NOT NULL,
                    score INT NOT NULL,  -- процент правильных ответов
                    total_questions INT NOT NULL,
                    correct_answers INT NOT NULL,
                    completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(userId) ON DELETE CASCADE,
                    FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )

            # Таблица пользовательских ответов (для показа после теста)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_answers (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    result_id INT NOT NULL,
                    question_id INT NOT NULL,
                    selected_answer_id INT DEFAULT NULL,
                    is_correct TINYINT(1) NOT NULL DEFAULT '0',
                    FOREIGN KEY (result_id) REFERENCES test_results(id) ON DELETE CASCADE,
                    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                    FOREIGN KEY (selected_answer_id) REFERENCES answers(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
                """
            )

            conn.commit()
            logger.info("DB initialized")
    except Error as error:
        logger.error("DB init error: {}".format(error))
        conn.rollback()
    finally:
        conn.close()

class Users:
    @staticmethod
    def isUserExist(userId: int) -> bool:
        """Проверяет существование пользователя"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("SELECT userId FROM users WHERE userId = %s", (userId,))
            return cursor.fetchone() is not None
        finally:
            connect.close()

    @staticmethod
    def addUser(userId: int, userName: str):
        """Добавляет нового пользователя"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("INSERT INTO users (userId, userName) VALUES (%s, %s)", (userId, userName))
            connect.commit()
            return True
        except Error as error:
            logger.error(f"addUser error {userId}: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def updateUserInfo(userId: int, firstName: str = None, lastName: str = None, middleName: str = None, phone: str = None):
        """Обновляет информацию о пользователе"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            update_fields = []
            values = []

            if firstName is not None:
                update_fields.append("firstName = %s")
                values.append(firstName)
            if lastName is not None:
                update_fields.append("lastName = %s")
                values.append(lastName)
            if middleName is not None:
                update_fields.append("middleName = %s")
                values.append(middleName)
            if phone is not None:
                update_fields.append("phone = %s")
                values.append(phone)

            if update_fields:
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE userId = %s"
                values.append(userId)
                cursor.execute(query, values)
                connect.commit()
                return cursor.rowcount > 0
            return False
        except Error as error:
            logger.error(f"updateUserInfo error {userId}: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def getUserFullInfo(userId: int):
        """Получить полную информацию о пользователе"""
        connect = getConnection()
        if connect is None:
            return None
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE userId = %s", (userId,))
            return cursor.fetchone()
        finally:
            connect.close()

    @staticmethod
    def setAdmin(userId: int):
        """Назначить пользователя администратором"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("UPDATE users SET role = 'admin' WHERE userId = %s", (userId,))
            connect.commit()
            return cursor.rowcount > 0
        except Error as error:
            logger.error(f"setAdmin error {userId}: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def ensure_user(userId: int, userName: str):
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("SELECT userId FROM users WHERE userId = %s", (userId,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO users (userId, userName) VALUES (%s, %s)", (userId, userName))
                connect.commit()
            return True
        except Error as error:
            logger.error(f"ensure_user error {userId}: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def isBlocked(userId: int) -> bool:
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("SELECT isBlocked FROM users WHERE userId = %s", (userId,))
            row = cursor.fetchone()
            return bool(row and row[0])
        finally:
            connect.close()

    @staticmethod
    def getAllUsers():
        """Получить всех пользователей"""
        connect = getConnection()
        if connect is None:
            return []
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users ORDER BY joinDate DESC")
            return cursor.fetchall()
        finally:
            connect.close()

    @staticmethod
    def getUserById(userId: int):
        """Получить пользователя по ID"""
        connect = getConnection()
        if connect is None:
            return None
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE userId = %s", (userId,))
            return cursor.fetchone()
        finally:
            connect.close()

    @staticmethod
    def blockUser(userId: int):
        """Заблокировать пользователя"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("UPDATE users SET isBlocked = 1 WHERE userId = %s", (userId,))
            connect.commit()
            return cursor.rowcount > 0
        except Error as error:
            logger.error(f"Ошибка блокировки пользователя {userId}: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def unblockUser(userId: int):
        """Разблокировать пользователя"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("UPDATE users SET isBlocked = 0 WHERE userId = %s", (userId,))
            connect.commit()
            return cursor.rowcount > 0
        except Error as error:
            logger.error(f"Ошибка разблокировки пользователя {userId}: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def deleteUser(userId: int):
        """Удалить пользователя"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("DELETE FROM users WHERE userId = %s", (userId,))
            connect.commit()
            return cursor.rowcount > 0
        except Error as error:
            logger.error(f"Ошибка удаления пользователя {userId}: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def getStats():
        """Получить статистику"""
        connect = getConnection()
        if connect is None:
            return {}
        try:
            cursor = connect.cursor()

            # Общее количество пользователей
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            # Заблокированные пользователи
            cursor.execute("SELECT COUNT(*) FROM users WHERE isBlocked = 1")
            blocked_users = cursor.fetchone()[0]

            # Администраторы
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admins_count = cursor.fetchone()[0]

            # Новые пользователи за последние 7 дней
            cursor.execute("SELECT COUNT(*) FROM users WHERE joinDate >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
            new_users_week = cursor.fetchone()[0]

            return {
                'total_users': total_users,
                'blocked_users': blocked_users,
                'admins_count': admins_count,
                'new_users_week': new_users_week
            }
        finally:
            connect.close()


class Categories:
    @staticmethod
    def addCategory(name: str, description: str = None):
        """Добавить категорию"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("INSERT INTO categories (name, description) VALUES (%s, %s)",
                         (name, description))
            connect.commit()
            return cursor.lastrowid
        except Error as error:
            logger.error(f"addCategory error: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def getAllCategories(active_only: bool = True):
        """Получить все категории"""
        connect = getConnection()
        if connect is None:
            return []
        try:
            cursor = connect.cursor(dictionary=True)
            query = "SELECT * FROM categories"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY name"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            connect.close()

    @staticmethod
    def deleteCategory(category_id: int):
        """Удалить категорию"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("UPDATE categories SET is_active = 0 WHERE id = %s", (category_id,))
            connect.commit()
            return cursor.rowcount > 0
        except Error as error:
            logger.error(f"deleteCategory error {category_id}: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def getCategoryById(category_id: int):
        """Получить категорию по ID"""
        connect = getConnection()
        if connect is None:
            return None
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("SELECT * FROM categories WHERE id = %s AND is_active = 1", (category_id,))
            return cursor.fetchone()
        finally:
            connect.close()


class Tests:
    @staticmethod
    def addTest(category_id: int, title: str, description: str = None):
        """Добавить тест"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("INSERT INTO tests (category_id, title, description) VALUES (%s, %s, %s)",
                         (category_id, title, description))
            connect.commit()
            return cursor.lastrowid
        except Error as error:
            logger.error(f"addTest error: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def getTestsByCategory(category_id: int, active_only: bool = True):
        """Получить тесты по категории"""
        connect = getConnection()
        if connect is None:
            return []
        try:
            cursor = connect.cursor(dictionary=True)
            query = "SELECT * FROM tests WHERE category_id = %s"
            if active_only:
                query += " AND is_active = 1"
            query += " ORDER BY title"
            cursor.execute(query, (category_id,))
            return cursor.fetchall()
        finally:
            connect.close()

    @staticmethod
    def getAllTests(active_only: bool = True):
        """Получить все тесты"""
        connect = getConnection()
        if connect is None:
            return []
        try:
            cursor = connect.cursor(dictionary=True)
            query = """
                SELECT t.*, c.name as category_name
                FROM tests t
                JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            """
            if active_only:
                query += " AND t.is_active = 1 AND c.is_active = 1"
            query += " ORDER BY c.name, t.title"
            cursor.execute(query)
            return cursor.fetchall()
        finally:
            connect.close()

    @staticmethod
    def getTestById(test_id: int):
        """Получить тест по ID"""
        connect = getConnection()
        if connect is None:
            return None
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("""
                SELECT t.*, c.name as category_name
                FROM tests t
                JOIN categories c ON t.category_id = c.id
                WHERE t.id = %s AND t.is_active = 1 AND c.is_active = 1
            """, (test_id,))
            return cursor.fetchone()
        finally:
            connect.close()

    @staticmethod
    def deleteTest(test_id: int):
        """Удалить тест"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("UPDATE tests SET is_active = 0 WHERE id = %s", (test_id,))
            connect.commit()
            return cursor.rowcount > 0
        except Error as error:
            logger.error(f"deleteTest error {test_id}: {error}")
            return False
        finally:
            connect.close()


class Questions:
    @staticmethod
    def addQuestion(test_id: int, question_text: str, image_path: str = None, question_order: int = None):
        """Добавить вопрос"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            if question_order is None:
                # Получить максимальный порядок для теста
                cursor.execute("SELECT MAX(question_order) FROM questions WHERE test_id = %s", (test_id,))
                max_order = cursor.fetchone()[0]
                question_order = (max_order or 0) + 1

            cursor.execute("""
                INSERT INTO questions (test_id, question_text, image_path, question_order)
                VALUES (%s, %s, %s, %s)
            """, (test_id, question_text, image_path, question_order))
            connect.commit()
            return cursor.lastrowid
        except Error as error:
            logger.error(f"addQuestion error: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def getQuestionsByTest(test_id: int):
        """Получить вопросы теста"""
        connect = getConnection()
        if connect is None:
            return []
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM questions
                WHERE test_id = %s
                ORDER BY question_order
            """, (test_id,))
            return cursor.fetchall()
        finally:
            connect.close()

    @staticmethod
    def getQuestionById(question_id: int):
        """Получить вопрос по ID"""
        connect = getConnection()
        if connect is None:
            return None
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
            return cursor.fetchone()
        finally:
            connect.close()


class Answers:
    @staticmethod
    def addAnswer(question_id: int, answer_text: str, is_correct: bool = False, answer_order: int = None):
        """Добавить ответ"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            if answer_order is None:
                # Получить максимальный порядок для вопроса
                cursor.execute("SELECT MAX(answer_order) FROM answers WHERE question_id = %s", (question_id,))
                max_order = cursor.fetchone()[0]
                answer_order = (max_order or 0) + 1

            cursor.execute("""
                INSERT INTO answers (question_id, answer_text, is_correct, answer_order)
                VALUES (%s, %s, %s, %s)
            """, (question_id, answer_text, is_correct, answer_order))
            connect.commit()
            return cursor.lastrowid
        except Error as error:
            logger.error(f"addAnswer error: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def getAnswersByQuestion(question_id: int):
        """Получить ответы на вопрос"""
        connect = getConnection()
        if connect is None:
            return []
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM answers
                WHERE question_id = %s
                ORDER BY answer_order
            """, (question_id,))
            return cursor.fetchall()
        finally:
            connect.close()

    @staticmethod
    def getCorrectAnswer(question_id: int):
        """Получить правильный ответ на вопрос"""
        connect = getConnection()
        if connect is None:
            return None
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM answers
                WHERE question_id = %s AND is_correct = 1
                LIMIT 1
            """, (question_id,))
            return cursor.fetchone()
        finally:
            connect.close()


class TestResults:
    @staticmethod
    def saveResult(user_id: int, test_id: int, score: int, total_questions: int, correct_answers: int):
        """Сохранить результат теста"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            cursor.execute("""
                INSERT INTO test_results (user_id, test_id, score, total_questions, correct_answers)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, test_id, score, total_questions, correct_answers))
            connect.commit()
            return cursor.lastrowid
        except Error as error:
            logger.error(f"saveResult error: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def saveUserAnswers(result_id: int, answers_data: list):
        """Сохранить ответы пользователя"""
        connect = getConnection()
        if connect is None:
            return False
        try:
            cursor = connect.cursor()
            for answer_data in answers_data:
                cursor.execute("""
                    INSERT INTO user_answers (result_id, question_id, selected_answer_id, is_correct)
                    VALUES (%s, %s, %s, %s)
                """, (result_id, answer_data['question_id'], answer_data['selected_answer_id'], answer_data['is_correct']))
            connect.commit()
            return True
        except Error as error:
            logger.error(f"saveUserAnswers error: {error}")
            return False
        finally:
            connect.close()

    @staticmethod
    def getUserResults(user_id: int, limit: int = 10):
        """Получить результаты пользователя"""
        connect = getConnection()
        if connect is None:
            return []
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("""
                SELECT tr.*, t.title as test_title, c.name as category_name
                FROM test_results tr
                JOIN tests t ON tr.test_id = t.id
                JOIN categories c ON t.category_id = c.id
                WHERE tr.user_id = %s
                ORDER BY tr.completed_at DESC
                LIMIT %s
            """, (user_id, limit))
            return cursor.fetchall()
        finally:
            connect.close()

    @staticmethod
    def getTestStats(test_id: int = None, period_days: int = None):
        """Получить статистику по тестам"""
        connect = getConnection()
        if connect is None:
            return {}
        try:
            cursor = connect.cursor()

            # Общее количество пройденных тестов
            query = "SELECT COUNT(*) FROM test_results WHERE 1=1"
            params = []

            if test_id:
                query += " AND test_id = %s"
                params.append(test_id)

            if period_days:
                query += " AND completed_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"
                params.append(period_days)

            cursor.execute(query, params)
            total_passed = cursor.fetchone()[0]

            # Средний балл
            query = "SELECT AVG(score) FROM test_results WHERE 1=1"
            params = []

            if test_id:
                query += " AND test_id = %s"
                params.append(test_id)

            if period_days:
                query += " AND completed_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"
                params.append(period_days)

            cursor.execute(query, params)
            avg_score = cursor.fetchone()[0] or 0

            # Количество уникальных пользователей
            query = "SELECT COUNT(DISTINCT user_id) FROM test_results WHERE 1=1"
            params = []

            if test_id:
                query += " AND test_id = %s"
                params.append(test_id)

            if period_days:
                query += " AND completed_at >= DATE_SUB(NOW(), INTERVAL %s DAY)"
                params.append(period_days)

            cursor.execute(query, params)
            unique_users = cursor.fetchone()[0]

            return {
                'total_passed': total_passed,
                'avg_score': round(avg_score, 1),
                'unique_users': unique_users
            }
        finally:
            connect.close()

    @staticmethod
    def getDetailedUserAnswers(result_id: int):
        """Получить детальные ответы пользователя по результату"""
        connect = getConnection()
        if connect is None:
            return []
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    q.question_text,
                    q.image_path,
                    ua.is_correct,
                    sa.answer_text as selected_answer,
                    ca.answer_text as correct_answer
                FROM user_answers ua
                JOIN questions q ON ua.question_id = q.id
                LEFT JOIN answers sa ON ua.selected_answer_id = sa.id
                LEFT JOIN answers ca ON ca.question_id = q.id AND ca.is_correct = 1
                WHERE ua.result_id = %s
                ORDER BY q.question_order
            """, (result_id,))
            return cursor.fetchall()
        finally:
            connect.close()

