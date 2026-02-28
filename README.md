# LocalFarmConnect 🌾

A Django-based e-commerce platform connecting local farmers with buyers, enabling direct sales of fresh agricultural products.

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [User Roles](#-user-roles)
- [API Endpoints](#-api-endpoints)
- [Database Schema](#-database-schema)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 Features

### **For Farmers**
- **Product Management**: Add, edit, and delete agricultural products
- **Category Organization**: Organize products by categories (Vegetables, Fruits, Dairy, etc.)
- **Order Management**: View and manage incoming orders
- **Status Updates**: Update order status (pending → confirmed → paid → shipped → delivered)
- **Revenue Tracking**: Monitor total sales and revenue

### **For Buyers**
- **Marketplace Browsing**: Browse products from local farmers
- **Search & Filter**: Search products and filter by category
- **Shopping Cart**: Add products to cart and manage quantities
- **Secure Checkout**: Simple checkout process with order creation
- **Order Tracking**: Track order status and history
- **Product Reviews**: Rate and review purchased products

### **Platform Features**
- **User Authentication**: Role-based registration (Farmer/Buyer)
- **Responsive Design**: Mobile-friendly interface using Tailwind CSS
- **Real-time Stock Management**: Automatic stock validation
- **Payment Tracking**: Integrated payment status management
- **Admin Panel**: Complete admin interface for platform management

## 🛠 Tech Stack

### **Backend**
- **Framework**: Django 4.2.28
- **Database**: PostgreSQL
- **Authentication**: Django's built-in auth system with custom user model
- **Forms**: Django forms with custom validation

### **Frontend**
- **Styling**: Tailwind CSS (via CDN)
- **Templates**: Django Template Engine
- **UI Components**: Custom responsive components
- **Icons**: Emoji icons for simplicity

### **Development Tools**
- **Version Control**: Git
- **Package Management**: pip
- **Virtual Environment**: venv

## 📁 Project Structure

```
localfarmconnect/
├── config/                 # Django project configuration
│   ├── __init__.py
│   ├── settings.py         # Main Django settings
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI configuration
│   └── asgi.py            # ASGI configuration
├── users/                 # Main Django app
│   ├── migrations/        # Database migrations
│   ├── templatetags/     # Custom template tags
│   ├── __init__.py
│   ├── admin.py          # Admin interface configuration
│   ├── apps.py           # App configuration
│   ├── forms.py          # Django forms
│   ├── models.py         # Database models
│   ├── tests.py          # Test cases
│   ├── urls.py           # App URL configuration
│   └── views.py          # View logic
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   └── users/           # User-specific templates
├── manage.py             # Django management script
├── venv/                # Virtual environment
└── README.md            # This file
```

## 🚀 Installation

### **Prerequisites**
- Python 3.8+
- PostgreSQL
- Git
- pip

### **Step 1: Clone the Repository**
```bash
git clone <repository-url>
cd localfarmconnect
```

### **Step 2: Set Up Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### **Step 3: Install Dependencies**
```bash
pip install django psycopg2-binary pillow
```

### **Step 4: Database Setup**
1. Create PostgreSQL database:
```sql
CREATE DATABASE localfarmconnect;
CREATE USER moturi311 WITH PASSWORD 'soweto311';
GRANT ALL PRIVILEGES ON DATABASE localfarmconnect TO moturi311;
```

2. Configure settings in `config/settings.py` (already configured for local development)

### **Step 5: Run Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

### **Step 6: Create Superuser**
```bash
python manage.py createsuperuser
```

### **Step 7: Seed Categories (Optional)**
```python
python manage.py shell
>>> from users.models import Category
>>> categories = ['vegetables', 'fruits', 'grains', 'dairy', 'poultry', 'herbs', 'nuts', 'legumes', 'spices', 'other']
>>> for cat in categories:
...     Category.objects.get_or_create(name=cat)
```

### **Step 8: Run Development Server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## ⚙️ Configuration

### **Database Settings**
Located in `config/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'localfarmconnect',
        'USER': 'moturi311',
        'PASSWORD': 'soweto311',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### **Media Files**
- Media URL: `/media/`
- Upload path: `BASE_DIR / 'media'`
- Product images uploaded to `products/` subdirectory

### **Authentication**
- Custom user model: `users.User`
- User types: `farmer`, `buyer`
- Login URL: `/login/`
- Redirect URLs configured per user type

## 🎯 Usage

### **For Farmers**
1. **Register**: Choose "Farmer" as user type
2. **Add Products**: Navigate to Dashboard → Add Product
3. **Manage Orders**: View and update order status from Orders page
4. **Track Revenue**: Monitor sales from Dashboard

### **For Buyers**
1. **Register**: Choose "Buyer" as user type
2. **Browse Products**: Explore marketplace with search and filters
3. **Add to Cart**: Select products and quantities
4. **Checkout**: Complete purchase process
5. **Track Orders**: Monitor order status and leave reviews

### **For Administrators**
1. **Access Admin**: `/admin/` with superuser credentials
2. **Manage Users**: Create and manage user accounts
3. **Manage Categories**: Add/edit product categories
4. **Monitor Orders**: Overview of all platform transactions

## 👥 User Roles

### **Farmers**
- Can create and manage products
- Can view and update order status
- Cannot purchase products
- Have access to farmer-specific dashboard

### **Buyers**
- Can browse and purchase products
- Can leave reviews for purchased products
- Can track order history
- Have access to buyer-specific dashboard

### **Administrators**
- Full platform management access
- User management capabilities
- Category management
- Order oversight

## 🌐 URL Structure

### **Public Routes**
- `/` - Marketplace (product listing)
- `/products/<id>/` - Product details
- `/products/<id>/review/` - Product review form
- `/register/` - User registration
- `/login/` - User login
- `/logout/` - User logout

### **Farmer Routes**
- `/farmer/products/` - Product management
- `/farmer/products/add/` - Add new product
- `/farmer/products/<id>/edit/` - Edit product
- `/farmer/products/<id>/delete/` - Delete product
- `/farmer/orders/` - Order management
- `/farmer/orders/<id>/` - Order details
- `/farmer/orders/<id>/status/` - Update order status

### **Buyer Routes**
- `/cart/` - Shopping cart
- `/cart/add/<id>/` - Add to cart
- `/cart/remove/<id>/` - Remove from cart
- `/cart/update/` - Update cart quantities
- `/checkout/` - Checkout process
- `/buyer/orders/` - Order history
- `/buyer/orders/<id>/` - Order details
- `/buyer/orders/<id>/pay/` - Payment processing

## 🗄️ Database Schema

### **Core Models**

#### **User System**
- **User**: Custom user model extending AbstractUser
  - `user_type`: 'farmer' or 'buyer'
  - `phone`: Optional phone number
- **FarmerProfile**: One-to-one with User
  - `farm_name`: Farm business name
  - `location`: Farm location
  - `description`: Farm description

#### **Product Management**
- **Category**: Product categorization
  - `name`: Unique category name
- **Product**: Farmers' products
  - `farmer`: Foreign key to FarmerProfile
  - `category`: Foreign key to Category
  - `name`, `description`, `price`, `quantity_available`, `image`

#### **Order System**
- **Order**: Order headers
  - `buyer`: Foreign key to User (buyer type)
  - `status`: Order status workflow
  - `created_at`: Order timestamp
- **OrderItem**: Order line items
  - `order`: Foreign key to Order
  - `product`: Foreign key to Product
  - `quantity`, `price_at_time`
- **Payment**: Payment tracking
  - `order`: One-to-one with Order
  - `transaction_id`, `amount`, `status`

#### **Review System**
- **Review**: Product reviews
  - `product`: Foreign key to Product
  - `buyer`: Foreign key to User (buyer type)
  - `rating`, `comment`, `created_at`

## 🧪 Testing

### **Run Tests**
```bash
python manage.py test
```

### **Test Coverage**
- User authentication and registration
- Product CRUD operations
- Order processing workflow
- Cart functionality
- Category management

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature-name`
3. **Make your changes**
4. **Run tests**: Ensure all tests pass
5. **Commit changes**: `git commit -m 'Add feature'`
6. **Push to branch**: `git push origin feature-name`
7. **Create Pull Request**

### **Development Guidelines**
- Follow PEP 8 for Python code
- Use meaningful commit messages
- Add tests for new features
- Update documentation as needed
- Maintain responsive design standards

## 📝 Deployment

### **Production Considerations**
- Set `DEBUG = False` in production
- Configure proper database settings
- Set up static file serving
- Configure email backend for notifications
- Set up proper logging
- Use environment variables for sensitive data

### **Environment Variables**
```bash
export SECRET_KEY='your-secret-key'
export DATABASE_URL='your-database-url'
export DEBUG=False
```

## 🔒 Security Features

- **CSRF Protection**: Enabled by Django
- **SQL Injection Prevention**: Django ORM protection
- **XSS Protection**: Django template auto-escaping
- **Authentication**: Secure password hashing
- **Authorization**: Role-based access control
- **File Upload Security**: Restricted file types and validation

## 📊 Performance

- **Database Optimization**: Select_related and prefetch_related
- **Pagination**: Implemented for large datasets
- **Static Files**: Optimized CSS delivery
- **Image Handling**: Proper image upload and serving
- **Caching**: Session-based cart for performance

## 🐛 Troubleshooting

### **Common Issues**

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in settings.py

2. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Verify STATIC_URL and STATIC_ROOT settings

3. **Images Not Uploading**
   - Check MEDIA_ROOT and MEDIA_URL settings
   - Verify file permissions

4. **Category Dropdown Empty**
   - Ensure categories exist in database
   - Run category seeding script

### **Debug Mode**
Enable debug mode in `config/settings.py`:
```python
DEBUG = True
```

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check existing documentation
- Review Django documentation at https://docs.djangoproject.com/

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django Team for the excellent framework
- Tailwind CSS for the utility-first CSS framework
- PostgreSQL for the robust database system
- The open-source community for inspiration and tools

---

**LocalFarmConnect** - Connecting Farms to Communities 🌱🛒
