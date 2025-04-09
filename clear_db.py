from app import app, db, User, Content, Question, Answer

def clear_database():
    with app.app_context():
        # Delete all records from each table
        print("Clearing database...")
        
        # Delete in reverse order of dependencies
        Answer.query.delete()
        print("Cleared Answer table")
        
        Question.query.delete()
        print("Cleared Question table")
        
        Content.query.delete()
        print("Cleared Content table")
        
        User.query.delete()
        print("Cleared User table")
        
        # Commit the changes
        db.session.commit()
        print("Database cleared successfully!")

if __name__ == "__main__":
    # Ask for confirmation
    response = input("This will delete ALL data from the database. Are you sure? (yes/no): ")
    
    if response.lower() == 'yes':
        clear_database()
    else:
        print("Operation cancelled.") 