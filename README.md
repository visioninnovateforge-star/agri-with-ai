# Agriculture Insights Platform

A comprehensive full-stack web application for agriculture insights, featuring ML-powered predictions, role-based dashboards, and real-time alerts for farmers, agronomists, and researchers.

## 🚀 Features

### Core Functionality
- **Multi-Role Authentication**: Secure signup/login for Farmers, Agronomists, and Researchers
- **ML-Powered Predictions**: Yield prediction and crop health analysis using machine learning
- **Real-time Alerts**: Smart notifications for irrigation, pest control, and weather conditions
- **Data Analytics**: Comprehensive insights and trend analysis for research purposes
- **Role-Based Dashboards**: Customized interfaces for each user type

### User Roles & Capabilities

#### 🌾 Farmers
- Upload field data (soil, water, crop information)
- Get ML-powered yield predictions
- Receive real-time alerts and recommendations
- View historical predictions and trends

#### 🔬 Agronomists
- Analyze farmer data and trends
- Validate and correct ML predictions
- Provide expert recommendations
- Monitor multiple farms and alerts

#### 📊 Researchers
- Access aggregated agricultural data
- Export datasets for analysis
- Generate research reports
- Analyze regional and seasonal trends

## 🛠 Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Supabase**: PostgreSQL database with real-time subscriptions
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type annotations
- **JWT**: Secure authentication and authorization
- **Scikit-learn**: Machine learning models for predictions

### Frontend
- **HTML5 + CSS3**: Semantic markup and modern styling
- **Tailwind CSS**: Utility-first CSS framework
- **JavaScript**: Interactive frontend functionality
- **Jinja2**: Server-side templating

### Database
- **PostgreSQL**: Robust relational database via Supabase
- **Row Level Security**: Database-level access control
- **Real-time subscriptions**: Live data updates

## 📁 Project Structure

```
agriculture-insights/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models and schemas
│   │   ├── routes/          # API endpoints
│   │   ├── ml_models/       # Machine learning models
│   │   └── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variables template
├── frontend/
│   ├── templates/           # HTML templates
│   ├── static/
│   │   ├── css/            # Stylesheets
│   │   └── js/             # JavaScript files
│   └── ...
├── database/
│   ├── schema.sql          # Database schema
│   └── setup.md            # Database setup instructions
├── deployment/
│   └── ...                 # Deployment configurations
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Supabase account
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/visioninnovateforge-star/agri-with-ai.git
   cd agri-with-ai
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

4. **Set up the database**
   - Create a Supabase project
   - Run the SQL commands from `database/schema.sql`
   - Update `.env` with your Supabase URL and key

5. **Generate ML models**
   ```bash
   cd app/ml_models
   python create_models.py
   ```

6. **Run the application**
   ```bash
   cd ../..
   uvicorn main:app --reload
   ```

7. **Open your browser**
   Navigate to `http://localhost:8000`

## 🔧 Configuration

### Supabase Setup
1. Create a new Supabase project
2. Navigate to SQL Editor and execute `database/schema.sql`
3. Get your project URL and anon key from Settings > API
4. Update your `.env` file with these credentials

### ML Models
The application includes sample ML models for:
- **Yield Prediction**: Based on soil, weather, and crop data
- **Crop Health Analysis**: Using NDVI and environmental factors

To create your own models, modify `backend/app/ml_models/create_models.py`

## 📊 API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Farmer APIs
- `POST /api/farmer/field-data` - Submit field data
- `GET /api/farmer/predictions` - Get predictions
- `GET /api/farmer/alerts` - Get alerts

### Agronomist APIs
- `GET /api/agronomist/farmers` - List all farmers
- `POST /api/agronomist/predictions/validate` - Validate predictions
- `GET /api/agronomist/analytics/overview` - Get analytics

### Researcher APIs
- `GET /api/researcher/aggregate-data` - Get aggregated insights
- `GET /api/researcher/download-dataset` - Export data
- `GET /api/researcher/analytics/trends` - Get trend analysis

### ML APIs
- `POST /api/ml/predict-yield` - Yield prediction
- `POST /api/ml/crop-health` - Crop health analysis
- `GET /api/ml/alerts` - Generate smart alerts

## 🎨 Frontend

The frontend uses a modern, responsive design built with:
- **Tailwind CSS** for styling
- **HTML5** semantic markup
- **JavaScript** for interactivity

### Key Pages
- Landing page with platform overview
- Role-specific dashboards
- Data input forms
- Analytics and reporting interfaces

## 🚀 Deployment

### Backend Deployment (Railway/Render)
1. Connect your GitHub repository
2. Set environment variables
3. Deploy with automatic builds

### Database (Supabase)
- Managed PostgreSQL with automatic backups
- Built-in authentication and real-time features
- Row-level security for data protection

### Frontend Options
1. **Integrated**: Served via FastAPI templates
2. **Separate**: Deploy to Vercel/Netlify

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Supabase** for the excellent backend-as-a-service platform
- **FastAPI** for the intuitive and fast web framework
- **Tailwind CSS** for the utility-first CSS framework
- **Scikit-learn** for machine learning capabilities

## 📞 Support

For support, email support@agriculture-insights.com or join our Slack channel.

## 🗺 Roadmap

- [ ] Mobile app development
- [ ] Advanced ML models with deep learning
- [ ] IoT sensor integration
- [ ] Satellite imagery analysis
- [ ] Multi-language support
- [ ] Real-time chat for agronomist consultation

---

**Built with ❤️ for the agriculture community**