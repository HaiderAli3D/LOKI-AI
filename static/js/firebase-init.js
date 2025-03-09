/**
 * Firebase initialization for the web client
 * This file initializes Firebase and makes it available to other scripts
 */

// Firebase configuration placeholder - these values should be replaced with actual Firebase project values
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
  appId: "YOUR_APP_ID",
  measurementId: "YOUR_MEASUREMENT_ID"
};

// Initialize Firebase
// This code should only run if the Firebase SDK is loaded
document.addEventListener('DOMContentLoaded', function() {
  if (typeof firebase !== 'undefined') {
    try {
      // Initialize Firebase
      firebase.initializeApp(firebaseConfig);
      
      console.log('Firebase initialized successfully');
      
      // Initialize Firebase Analytics if available
      if (firebase.analytics) {
        firebase.analytics();
      }
      
      // Listen for auth state changes
      firebase.auth().onAuthStateChanged(function(user) {
        if (user) {
          console.log('User is signed in with Firebase:', user.email);
        } else {
          console.log('No user is signed in with Firebase');
        }
      });
      
    } catch (error) {
      console.error('Error initializing Firebase:', error);
    }
  } else {
    console.warn('Firebase SDK not loaded. Authentication features requiring direct Firebase interaction will not work.');
  }
});

/**
 * This function provides a way to sign in with email and password using Firebase directly
 * It can be used as an alternative to the backend authentication
 */
function firebaseSignInWithEmailAndPassword(email, password) {
  return new Promise((resolve, reject) => {
    if (typeof firebase === 'undefined' || !firebase.auth) {
      reject(new Error('Firebase SDK not loaded'));
      return;
    }
    
    firebase.auth().signInWithEmailAndPassword(email, password)
      .then((userCredential) => {
        resolve(userCredential.user);
      })
      .catch((error) => {
        console.error('Firebase sign in error:', error.code, error.message);
        reject(error);
      });
  });
}

/**
 * This function provides a way to create a new user with email and password using Firebase directly
 * It can be used as an alternative to the backend registration
 */
function firebaseCreateUserWithEmailAndPassword(email, password) {
  return new Promise((resolve, reject) => {
    if (typeof firebase === 'undefined' || !firebase.auth) {
      reject(new Error('Firebase SDK not loaded'));
      return;
    }
    
    firebase.auth().createUserWithEmailAndPassword(email, password)
      .then((userCredential) => {
        resolve(userCredential.user);
      })
      .catch((error) => {
        console.error('Firebase create user error:', error.code, error.message);
        reject(error);
      });
  });
}

/**
 * This function provides a way to send a password reset email using Firebase directly
 */
function firebaseSendPasswordResetEmail(email) {
  return new Promise((resolve, reject) => {
    if (typeof firebase === 'undefined' || !firebase.auth) {
      reject(new Error('Firebase SDK not loaded'));
      return;
    }
    
    firebase.auth().sendPasswordResetEmail(email)
      .then(() => {
        resolve();
      })
      .catch((error) => {
        console.error('Firebase password reset error:', error.code, error.message);
        reject(error);
      });
  });
}

/**
 * This function signs out the current user from Firebase
 */
function firebaseSignOut() {
  return new Promise((resolve, reject) => {
    if (typeof firebase === 'undefined' || !firebase.auth) {
      reject(new Error('Firebase SDK not loaded'));
      return;
    }
    
    firebase.auth().signOut()
      .then(() => {
        resolve();
      })
      .catch((error) => {
        console.error('Firebase sign out error:', error);
        reject(error);
      });
  });
}
