import sqlite3
from passlib.hash import sha512_crypt

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

class FreeNASBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        # db_path = "/config/data/freenas-v1.db"
        db_path = "TrueNASdata/freenas-v1.db"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Adjust the query based on the actual FreeNAS schema
            cursor.execute("SELECT bsdusr_username, bsdusr_unixhash FROM account_bsdusers WHERE bsdusr_username=? or bsdusr_email=?", (username, username))
            
            result = cursor.fetchone()
            
            if result:
                db_username, db_password_hash = result
                
                # Verify password using crypt with SHA-512
                if sha512_crypt.verify(password, db_password_hash) == True:
                    # Check if user exists in Django's User model
                    try:
                        user = User.objects.get(username=db_username)
                    except ObjectDoesNotExist:
                        user = User(username=db_username)
                        user.set_unusable_password()  # Don't store password in Django
                        user.save()
                    
                    return user

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()
        
        return None  # Authentication failed

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None
