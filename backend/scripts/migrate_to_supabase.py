"""
Migrate data from local PostgreSQL to Supabase PostgreSQL
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Local PostgreSQL connection
LOCAL_DB_URL = "postgresql://jieru_0901:@localhost/lms_db"

# Supabase PostgreSQL connection (URL-encoded password)
SUPABASE_DB_URL = "postgresql://postgres:Ngjieren%4002@db.yxyplzwvunedqvcdetqg.supabase.co:5432/postgres"

local_engine = create_engine(LOCAL_DB_URL)
supabase_engine = create_engine(SUPABASE_DB_URL)

LocalSession = sessionmaker(bind=local_engine)
SupabaseSession = sessionmaker(bind=supabase_engine)

def migrate_table(table_name, columns):
    """Migrate a single table from local to Supabase"""
    local_db = LocalSession()
    
    try:
        # Get data from local
        result = local_db.execute(text(f"SELECT {', '.join(columns)} FROM {table_name}"))
        rows = result.fetchall()
        
        if not rows:
            print(f"  {table_name}: No data to migrate")
            return 0
        
        # Insert into Supabase - one connection per row to avoid transaction issues
        success_count = 0
        for row in rows:
            supabase_db = SupabaseSession()
            try:
                values = []
                for i, col in enumerate(columns):
                    val = row[i]
                    if val is None:
                        values.append("NULL")
                    elif isinstance(val, bool):
                        values.append("TRUE" if val else "FALSE")
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    else:
                        # Escape single quotes
                        val_str = str(val).replace("'", "''")
                        values.append(f"'{val_str}'")
                
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)}) ON CONFLICT DO NOTHING"
                supabase_db.execute(text(insert_sql))
                supabase_db.commit()
                success_count += 1
            except Exception as e:
                supabase_db.rollback()
                # Only print first few errors
                if success_count < 3:
                    print(f"    Error: {str(e)[:100]}")
            finally:
                supabase_db.close()
        
        print(f"  {table_name}: Migrated {success_count}/{len(rows)} rows")
        return success_count
        
    except Exception as e:
        print(f"  {table_name}: Error - {e}")
        return 0
    finally:
        local_db.close()

def reset_sequence(table_name, id_column="id"):
    """Reset the sequence for a table"""
    supabase_db = SupabaseSession()
    try:
        supabase_db.execute(text(f"SELECT setval(pg_get_serial_sequence('{table_name}', '{id_column}'), COALESCE(MAX({id_column}), 1)) FROM {table_name}"))
        supabase_db.commit()
    except Exception as e:
        print(f"  Could not reset sequence for {table_name}: {e}")
    finally:
        supabase_db.close()

def main():
    print("🚀 Migrating data from Local PostgreSQL to Supabase...")
    print("="*60)
    
    # Clear Supabase tables first
    print("\n1. Clearing Supabase tables...")
    supabase_db = SupabaseSession()
    try:
        supabase_db.execute(text("TRUNCATE TABLE quiz_attempts, topic_performance, student_enrollments, material_topics, materials, syllabus, courses, users RESTART IDENTITY CASCADE"))
        supabase_db.commit()
        print("   Tables cleared")
    except Exception as e:
        print(f"   Error clearing tables: {e}")
    finally:
        supabase_db.close()
    
    # Migrate tables in order (respecting foreign keys)
    print("\n2. Migrating tables...")
    
    # Users
    migrate_table("users", ["id", "email", "hashed_password", "full_name", "role", "is_active", "created_at", "updated_at"])
    reset_sequence("users")
    
    # Courses
    migrate_table("courses", ["id", "code", "name", "description", "lecturer_id", "is_active", "created_at", "updated_at"])
    reset_sequence("courses")
    
    # Syllabus
    migrate_table("syllabus", ["id", "course_id", "week_number", "topic", "content", "order_index", "created_at", "updated_at"])
    reset_sequence("syllabus")
    
    # Materials
    migrate_table("materials", ["id", "title", "url", "source", "type", "author", "published_date", "description", "snippet", "quality_score", "content_hash", "created_at"])
    reset_sequence("materials")
    
    # Material Topics
    migrate_table("material_topics", ["id", "material_id", "course_id", "week_number", "relevance_score", "approved_by_lecturer", "approved_by", "approved_at", "created_at"])
    reset_sequence("material_topics")
    
    # Student Enrollments
    migrate_table("student_enrollments", ["id", "student_id", "course_id", "enrolled_at", "is_active"])
    reset_sequence("student_enrollments")
    
    # Quiz Attempts
    migrate_table("quiz_attempts", ["id", "student_id", "course_id", "week_number", "question_type", "question_data", "student_answer", "score", "max_score", "is_correct", "feedback", "mode", "attempted_at", "time_spent_seconds"])
    reset_sequence("quiz_attempts")
    
    # Topic Performance (without created_at/updated_at as they may not exist in local)
    migrate_table("topic_performance", ["id", "student_id", "course_id", "week_number", "total_attempts", "correct_attempts", "average_score", "is_weak_topic", "mastery_level", "last_attempt_at"])
    reset_sequence("topic_performance")
    
    print("\n" + "="*60)
    print("✅ Migration complete!")
    
    # Verify counts
    print("\n3. Verifying data counts...")
    supabase_db = SupabaseSession()
    try:
        result = supabase_db.execute(text("""
            SELECT COUNT(*) as count, 'users' as tbl FROM users 
            UNION ALL SELECT COUNT(*), 'courses' FROM courses 
            UNION ALL SELECT COUNT(*), 'materials' FROM materials 
            UNION ALL SELECT COUNT(*), 'syllabus' FROM syllabus 
            UNION ALL SELECT COUNT(*), 'material_topics' FROM material_topics 
            UNION ALL SELECT COUNT(*), 'student_enrollments' FROM student_enrollments
        """))
        for row in result:
            print(f"   {row[1]}: {row[0]} rows")
    finally:
        supabase_db.close()

if __name__ == "__main__":
    main()
