# PortLeague

A Django web application for football fans to track matches, standings, and participate in interactive games like prediction polls and quizzes.

## Features

- **Live Football Data**: View upcoming fixtures, recent results, and league standings
- **Prediction Polls**: Vote on match outcomes and track your prediction accuracy
- **Football Quizzes**: Test your football knowledge with different difficulty levels
- **User Profiles**: Track your prediction and quiz performance 
- **Personalisation**: Follow your favorite team for customized content
- **Accessibility Features**: Dark/light mode and text size adjustments

## Technology Stack

- **Backend**: Django 5.0 and Python
- **Frontend**: CSS and JavaScript
- **Data Source**: Football-Data.org API
- **Database**: SQLite

## Local Setup & Installation

2. Create a virtual environment and activate it
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Run migrations
   ```
   python manage.py migrate
   ```

5. Populate teams data
   ```
   python manage.py populate_teams
   ```

6. Run the development server
   ```
   python manage.py runserver
   ```

7. Open your browser and navigate to http://127.0.0.1:8000

## Credits

- Football data provided by the [Football-Data.org API](https://www.football-data.org/) 