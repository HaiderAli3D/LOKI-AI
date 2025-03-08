# OCR A-Level Computer Science AI Tutor

An AI-powered tutor for OCR A-Level Computer Science students. This application helps students understand computer science concepts, practice their skills, and prepare for their exams.

## Features

- AI-powered tutoring with Claude AI
- Topic-specific learning sessions
- Progress tracking
- Exam practice with AI evaluation
- Resource library
- User authentication and subscription management
- Admin dashboard for content management

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Authentication**: Firebase Authentication
- **Payment Processing**: Stripe
- **File Storage**: AWS S3
- **AI**: Anthropic Claude
- **Deployment**: AWS Elastic Beanstalk

## Local Development Setup

### Prerequisites

- Python 3.9+
- PostgreSQL
- Firebase project
- Stripe account
- AWS account with S3 bucket
- Anthropic API key

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai-tutor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and fill in your configuration values.

5. Create the database:
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Run the development server:
   ```bash
   flask run
   ```

7. Access the application at http://localhost:5000

## Deployment to AWS Elastic Beanstalk

### Prerequisites

- AWS CLI installed and configured
- EB CLI installed

### Steps

1. Initialize Elastic Beanstalk:
   ```bash
   eb init -p python-3.9 ai-tutor
   ```

2. Create an environment:
   ```bash
   eb create ai-tutor-env
   ```

3. Configure environment variables:
   - Go to the AWS Elastic Beanstalk Console
   - Navigate to your environment
   - Go to Configuration > Software
   - Add all the environment variables from your `.env` file

4. Deploy the application:
   ```bash
   eb deploy
   ```

5. Open the application:
   ```bash
   eb open
   ```

## Project Structure

- `app.py`: Main application file
- `config/`: Configuration files
- `models/`: Database models
- `services/`: Service classes
- `routes/`: Route handlers
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS, images)
- `.ebextensions/`: Elastic Beanstalk configuration files

## Setting Up Third-Party Services

### Firebase Authentication

1. Create a Firebase project at https://console.firebase.google.com/
2. Enable Email/Password authentication
3. Generate a service account key and save it as `firebase-service-account.json`
4. Update the Firebase configuration in `.env`

### Stripe

1. Create a Stripe account at https://stripe.com/
2. Create subscription products and prices
3. Set up a webhook endpoint for `https://your-domain.com/api/subscription/webhook`
4. Update the Stripe configuration in `.env`

### AWS S3

1. Create an S3 bucket
2. Create an IAM user with S3 access
3. Update the AWS configuration in `.env`

### Anthropic Claude

1. Sign up for Anthropic API access at https://www.anthropic.com/
2. Generate an API key
3. Update the Anthropic configuration in `.env`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
