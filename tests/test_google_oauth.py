#!/usr/bin/env python3
"""
Google OAuth Integration Tests
Tests Google authentication flow and user account linking
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from app import app, db, User

class GoogleOAuthTestCase(unittest.TestCase):
    """Test Google OAuth integration"""
    
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['GOOGLE_CLIENT_ID'] = 'test_client_id'
        app.config['GOOGLE_CLIENT_SECRET'] = 'test_client_secret'
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create existing user for account linking test
        self.existing_user = User(
            email='existing@test.com',
            first_name='Existing',
            last_name='User',
            role='provider',
            auth_provider='local'
        )
        self.existing_user.set_password('testpass')
        db.session.add(self.existing_user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_google_login_redirect(self):
        """Test Google login initiates OAuth redirect"""
        with patch('app.google') as mock_google:
            mock_google.authorize_redirect.return_value = Mock()
            rv = self.app.get('/login/google')
            mock_google.authorize_redirect.assert_called_once()
    
    def test_google_login_without_config(self):
        """Test Google login when not configured"""
        # Temporarily remove Google config
        app.config['GOOGLE_CLIENT_ID'] = None
        
        rv = self.app.get('/login/google', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'not configured', rv.data)
        
        # Restore config
        app.config['GOOGLE_CLIENT_ID'] = 'test_client_id'
    
    @patch('app.google')
    def test_google_callback_new_user(self, mock_google):
        """Test Google callback creates new user"""
        # Mock Google token response
        mock_token = {
            'userinfo': {
                'sub': 'google_user_123',
                'email': 'newuser@gmail.com',
                'given_name': 'New',
                'family_name': 'User',
                'picture': 'https://example.com/pic.jpg'
            }
        }
        mock_google.authorize_access_token.return_value = mock_token
        
        rv = self.app.get('/callback/google', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        
        # Verify user was created
        new_user = User.query.filter_by(email='newuser@gmail.com').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.google_id, 'google_user_123')
        self.assertEqual(new_user.auth_provider, 'google')
        self.assertEqual(new_user.role, 'provider')  # Default role
        self.assertIsNotNone(new_user.profile_picture)
    
    @patch('app.google')
    def test_google_callback_account_linking(self, mock_google):
        """Test Google callback links to existing account"""
        # Mock Google token for existing user email
        mock_token = {
            'userinfo': {
                'sub': 'google_user_456',
                'email': 'existing@test.com',
                'given_name': 'Existing',
                'family_name': 'User',
                'picture': 'https://example.com/newpic.jpg'
            }
        }
        mock_google.authorize_access_token.return_value = mock_token
        
        rv = self.app.get('/callback/google', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        
        # Verify existing user was updated with Google info
        updated_user = User.query.filter_by(email='existing@test.com').first()
        self.assertEqual(updated_user.google_id, 'google_user_456')
        self.assertEqual(updated_user.auth_provider, 'google')
        self.assertEqual(updated_user.profile_picture, 'https://example.com/newpic.jpg')
    
    @patch('app.google')
    def test_google_callback_existing_google_user(self, mock_google):
        """Test Google callback for returning Google user"""
        # Create existing Google user
        google_user = User(
            email='googleuser@gmail.com',
            first_name='Google',
            last_name='User',
            role='provider',
            google_id='existing_google_123',
            auth_provider='google'
        )
        db.session.add(google_user)
        db.session.commit()
        
        # Mock returning user token
        mock_token = {
            'userinfo': {
                'sub': 'existing_google_123',
                'email': 'googleuser@gmail.com',
                'given_name': 'Google',
                'family_name': 'User',
                'picture': 'https://example.com/pic.jpg'
            }
        }
        mock_google.authorize_access_token.return_value = mock_token
        
        rv = self.app.get('/callback/google', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        
        # Verify user count didn't increase (no duplicate created)
        users = User.query.filter_by(email='googleuser@gmail.com').all()
        self.assertEqual(len(users), 1)
    
    @patch('app.google')
    def test_google_callback_error_handling(self, mock_google):
        """Test Google callback error handling"""
        # Mock OAuth error
        mock_google.authorize_access_token.side_effect = Exception("OAuth error")
        
        rv = self.app.get('/callback/google', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'authentication failed', rv.data)
    
    @patch('app.google')
    def test_google_callback_without_config(self, mock_google):
        """Test Google callback when not configured"""
        app.config['GOOGLE_CLIENT_ID'] = None
        
        rv = self.app.get('/callback/google', follow_redirects=True)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'not configured', rv.data)
        
        # Restore config
        app.config['GOOGLE_CLIENT_ID'] = 'test_client_id'
    
    def test_user_model_oauth_fields(self):
        """Test User model OAuth-specific fields"""
        user = User(
            email='oauth@test.com',
            first_name='OAuth',
            last_name='User',
            role='provider',
            google_id='oauth_123',
            profile_picture='https://example.com/pic.jpg',
            auth_provider='google'
        )
        
        # OAuth users don't need password
        self.assertIsNone(user.password_hash)
        self.assertFalse(user.check_password('anypassword'))
        
        # But can still be saved
        db.session.add(user)
        db.session.commit()
        
        saved_user = User.query.filter_by(email='oauth@test.com').first()
        self.assertIsNotNone(saved_user)
        self.assertEqual(saved_user.google_id, 'oauth_123')
        self.assertEqual(saved_user.auth_provider, 'google')

if __name__ == '__main__':
    unittest.main()