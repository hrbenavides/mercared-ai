"""
MercaRed AI — Backend principal
Flask + SQLite + Flask-Login
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, session
)
from flask_login import (
    LoginManager, UserMixin, login_user,
    logout_user, login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, json
from datetime import datetime, timedelta
import random

# ─── App config ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'mercared.db')

app = Flask(__name__)
app.secret_key = 'mercared-ai-secret-key-2025-umsa'

login_manager = LoginManager(app)
login_manager.login_view       = 'login'
login_manager.login_message    = 'Debes iniciar sesión para acceder.'

# ─── DB helpers ────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def query(sql, args=(), one=False, commit=False):
    conn = get_db()
    cur  = conn.execute(sql, args)
    if commit:
        conn.commit()
        rv = cur.lastrowid
    else:
        rv = cur.fetchone() if one else cur.fetchall()
    conn.close()
    return rv

# ─── Schema & seed ─────────────────────────────────────────────
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        email       TEXT    UNIQUE NOT NULL,
        password    TEXT    NOT NULL,
        role        TEXT    NOT NULL DEFAULT 'buyer',   -- buyer | seller | transporter | admin
        full_name   TEXT    NOT NULL,
        company     TEXT,
        phone       TEXT,
        city        TEXT    DEFAULT 'La Paz',
        avatar_initials TEXT,
        created_at  TEXT    DEFAULT (datetime('now')),
        is_active   INTEGER DEFAULT 1,
        bio         TEXT
    );

    CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        seller_id   INTEGER NOT NULL REFERENCES users(id),
        name        TEXT    NOT NULL,
        description TEXT,
        category    TEXT,
        price       REAL    NOT NULL,
        unit        TEXT    DEFAULT 'unidad',
        stock       INTEGER DEFAULT 0,
        min_order   INTEGER DEFAULT 1,
        image_emoji TEXT    DEFAULT '📦',
        is_active   INTEGER DEFAULT 1,
        created_at  TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS orders (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id     INTEGER NOT NULL REFERENCES users(id),
        seller_id    INTEGER NOT NULL REFERENCES users(id),
        transporter_id INTEGER REFERENCES users(id),
        status       TEXT    DEFAULT 'pending',
        -- pending | confirmed | preparing | in_transit | delivered | cancelled
        total        REAL    NOT NULL,
        notes        TEXT,
        delivery_address TEXT,
        created_at   TEXT    DEFAULT (datetime('now')),
        updated_at   TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id   INTEGER NOT NULL REFERENCES orders(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        qty        INTEGER NOT NULL,
        unit_price REAL    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS cart_items (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id),
        product_id INTEGER NOT NULL REFERENCES products(id),
        qty        INTEGER NOT NULL DEFAULT 1,
        added_at   TEXT    DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id),
        title      TEXT    NOT NULL,
        body       TEXT,
        type       TEXT    DEFAULT 'info',   -- info | warning | success | error
        is_read    INTEGER DEFAULT 0,
        created_at TEXT    DEFAULT (datetime('now'))
    );
    """)

    # Seed demo users if empty
    existing = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing == 0:
        users = [
            ('admin@mercared.bo',    generate_password_hash('admin123'),    'admin',       'Admin MercaRed',      'MercaRed AI',          '+591-7000000', 'La Paz',  'MA'),
            ('comprador@demo.bo',    generate_password_hash('demo123'),     'buyer',       'Carlos Mamani',       'Tienda San Martín',    '+591-7111111', 'La Paz',  'CM'),
            ('vendedor@demo.bo',     generate_password_hash('demo123'),     'seller',      'Distribuidora Norte', 'Distribuidora Norte',  '+591-7222222', 'El Alto', 'DN'),
            ('transporte@demo.bo',   generate_password_hash('demo123'),     'transporter', 'Luis Quispe',         'Express Logística',    '+591-7333333', 'La Paz',  'LQ'),
        ]
        c.executemany(
            "INSERT INTO users (email,password,role,full_name,company,phone,city,avatar_initials) VALUES (?,?,?,?,?,?,?,?)",
            users
        )

        # Seed products for seller (id=3)
        products = [
            (3,'Coca-Cola 2L','Bebida gaseosa','Bebidas',6.50,'unidad',200,12,'🥤'),
            (3,'Pepsi 2L','Bebida gaseosa','Bebidas',6.00,'unidad',180,12,'🥤'),
            (3,'Agua Mineral 500ml','Agua pura','Bebidas',2.50,'unidad',500,24,'💧'),
            (3,'Galletas Oreo 432g','Galletas surtido','Snacks',4.20,'paquete',150,6,'🍫'),
            (3,"Lay's Original 150g",'Papas fritas','Snacks',7.00,'bolsa',100,6,'🍟'),
            (3,'Papel Higiénico 6-pack','Higiene personal','Limpieza',18.00,'pack',80,3,'🧻'),
            (3,'Detergente Omo 1kg','Detergente en polvo','Limpieza',12.00,'bolsa',60,6,'🧴'),
            (3,'Caramelos Mix 100u','Surtido de caramelos','Dulces',2.80,'bolsa',300,12,'🍬'),
            (3,'Café Nescafé 200g','Café instantáneo','Bebidas',18.50,'frasco',90,6,'☕'),
            (3,'Azúcar 1kg','Azúcar blanca refinada','Abarrotes',5.50,'kg',200,6,'🍚'),
            (3,'Arroz 1kg','Arroz extra','Abarrotes',6.00,'kg',300,6,'🍚'),
            (3,'Aceite 1L','Aceite vegetal','Abarrotes',9.00,'litro',150,6,'🫙'),
        ]
        c.executemany(
            "INSERT INTO products (seller_id,name,description,category,price,unit,stock,min_order,image_emoji) VALUES (?,?,?,?,?,?,?,?,?)",
            products
        )

        # Seed some orders
        statuses = ['delivered','delivered','in_transit','confirmed','preparing']
        for i, st in enumerate(statuses):
            days_ago = i + 1
            created  = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            oid = c.execute(
                "INSERT INTO orders (buyer_id,seller_id,status,total,delivery_address,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                (2, 3, st, round(random.uniform(80,600),2), 'Av. Buenos Aires 123, La Paz', created, created)
            ).lastrowid
            c.execute(
                "INSERT INTO order_items (order_id,product_id,qty,unit_price) VALUES (?,?,?,?)",
                (oid, random.randint(1,8), random.randint(6,24), round(random.uniform(3,20),2))
            )

        # Seed notifications for buyer
        notifs = [
            (2,'Stock bajo detectado','Coca-Cola 2L quedará sin stock en ~3 días según tu historial.','warning'),
            (2,'Pedido entregado','Tu pedido #0001 fue entregado exitosamente.','success'),
            (2,'Oferta especial','Distribuidora Norte ofrece 15% de descuento en bebidas esta semana.','info'),
        ]
        c.executemany(
            "INSERT INTO notifications (user_id,title,body,type) VALUES (?,?,?,?)",
            notifs
        )
        notifs_seller = [
            (3,'Nuevo pedido recibido','Tienda San Martín realizó un pedido de Bs. 156.00.','info'),
            (3,'Stock crítico','Coca-Cola 2L — quedan 12 unidades en almacén.','warning'),
        ]
        c.executemany(
            "INSERT INTO notifications (user_id,title,body,type) VALUES (?,?,?,?)",
            notifs_seller
        )

    conn.commit()
    conn.close()

# ─── User model ────────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, row):
        self.id              = row['id']
        self.email           = row['email']
        self.role            = row['role']
        self.full_name       = row['full_name']
        self.company         = row['company']
        self.phone           = row['phone']
        self.city            = row['city']
        self.avatar_initials = row['avatar_initials'] or row['full_name'][:2].upper()
        self.created_at      = row['created_at']
        self.bio             = row['bio']

@login_manager.user_loader
def load_user(user_id):
    row = query("SELECT * FROM users WHERE id=?", (user_id,), one=True)
    return User(row) if row else None

# ─── Helpers ───────────────────────────────────────────────────
ROLE_LABELS = {
    'buyer':       'Comprador',
    'seller':      'Vendedor / Distribuidor',
    'transporter': 'Transportista',
    'admin':       'Administrador',
}
ROLE_ICONS = {
    'buyer': '🏪', 'seller': '🏭', 'transporter': '🚚', 'admin': '⚙️'
}

def notif_count():
    if not current_user.is_authenticated:
        return 0
    return query("SELECT COUNT(*) as c FROM notifications WHERE user_id=? AND is_read=0",
                 (current_user.id,), one=True)['c']

app.jinja_env.globals['notif_count'] = notif_count
app.jinja_env.globals['ROLE_LABELS'] = ROLE_LABELS
app.jinja_env.globals['ROLE_ICONS']  = ROLE_ICONS
app.jinja_env.globals['now']         = datetime.now

# ─── PUBLIC ROUTES ──────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        remember = bool(request.form.get('remember'))
        row = query("SELECT * FROM users WHERE email=? AND is_active=1", (email,), one=True)
        if row and check_password_hash(row['password'], password):
            user = User(row)
            login_user(user, remember=remember)
            flash(f'Bienvenido, {user.full_name}!', 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))
        flash('Correo o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email     = request.form.get('email','').strip().lower()
        password  = request.form.get('password','')
        password2 = request.form.get('password2','')
        full_name = request.form.get('full_name','').strip()
        role      = request.form.get('role','buyer')
        company   = request.form.get('company','').strip()
        phone     = request.form.get('phone','').strip()
        city      = request.form.get('city','La Paz').strip()

        errors = []
        if not email or '@' not in email:
            errors.append('Correo inválido.')
        if len(password) < 6:
            errors.append('La contraseña debe tener al menos 6 caracteres.')
        if password != password2:
            errors.append('Las contraseñas no coinciden.')
        if not full_name:
            errors.append('El nombre es requerido.')
        if role not in ('buyer','seller','transporter'):
            errors.append('Tipo de usuario inválido.')
        if query("SELECT id FROM users WHERE email=?", (email,), one=True):
            errors.append('Ese correo ya está registrado.')

        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            initials = ''.join(w[0].upper() for w in full_name.split()[:2])
            uid = query(
                "INSERT INTO users (email,password,role,full_name,company,phone,city,avatar_initials) VALUES (?,?,?,?,?,?,?,?)",
                (email, generate_password_hash(password), role, full_name, company, phone, city, initials),
                commit=True
            )
            # Welcome notification
            query(
                "INSERT INTO notifications (user_id,title,body,type) VALUES (?,?,?,?)",
                (uid, '¡Bienvenido a MercaRed AI!',
                 f'Hola {full_name}, tu cuenta fue creada exitosamente. Comienza explorando la plataforma.', 'success'),
                commit=True
            )
            row = query("SELECT * FROM users WHERE id=?", (uid,), one=True)
            login_user(User(row))
            flash('¡Cuenta creada exitosamente!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('index'))

# ─── DASHBOARD (router) ────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    role = current_user.role
    if role == 'buyer':
        return redirect(url_for('buyer_home'))
    elif role == 'seller':
        return redirect(url_for('seller_home'))
    elif role == 'transporter':
        return redirect(url_for('transporter_home'))
    else:
        return redirect(url_for('admin_home'))

# ─── BUYER ──────────────────────────────────────────────────────
@app.route('/buyer')
@login_required
def buyer_home():
    if current_user.role != 'buyer':
        return redirect(url_for('dashboard'))
    # Recent orders
    orders = query("""
        SELECT o.*, u.full_name as seller_name, u.company as seller_company
        FROM orders o JOIN users u ON o.seller_id=u.id
        WHERE o.buyer_id=?
        ORDER BY o.created_at DESC LIMIT 5
    """, (current_user.id,))
    # Products (catalogue)
    products = query("SELECT p.*, u.full_name as seller_name FROM products p JOIN users u ON p.seller_id=u.id WHERE p.is_active=1 LIMIT 12")
    # Cart count
    cart_count = query("SELECT COALESCE(SUM(qty),0) as c FROM cart_items WHERE user_id=?", (current_user.id,), one=True)['c']
    notifs = query("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (current_user.id,))
    stats = {
        'total_orders': query("SELECT COUNT(*) as c FROM orders WHERE buyer_id=?", (current_user.id,), one=True)['c'],
        'delivered':    query("SELECT COUNT(*) as c FROM orders WHERE buyer_id=? AND status='delivered'", (current_user.id,), one=True)['c'],
        'pending':      query("SELECT COUNT(*) as c FROM orders WHERE buyer_id=? AND status NOT IN ('delivered','cancelled')", (current_user.id,), one=True)['c'],
    }
    return render_template('buyer/home.html', orders=orders, products=products,
                           cart_count=cart_count, notifs=notifs, stats=stats)

@app.route('/buyer/catalogue')
@login_required
def buyer_catalogue():
    if current_user.role != 'buyer': return redirect(url_for('dashboard'))
    category = request.args.get('category','')
    search   = request.args.get('q','')
    sql = "SELECT p.*, u.full_name as seller_name, u.company FROM products p JOIN users u ON p.seller_id=u.id WHERE p.is_active=1"
    args = []
    if category:
        sql += " AND p.category=?"; args.append(category)
    if search:
        sql += " AND p.name LIKE ?"; args.append(f'%{search}%')
    sql += " ORDER BY p.name"
    products   = query(sql, args)
    categories = query("SELECT DISTINCT category FROM products WHERE is_active=1 ORDER BY category")
    cart_count = query("SELECT COALESCE(SUM(qty),0) as c FROM cart_items WHERE user_id=?", (current_user.id,), one=True)['c']
    return render_template('buyer/catalogue.html', products=products,
                           categories=categories, cart_count=cart_count,
                           active_cat=category, search=search)

@app.route('/buyer/cart', methods=['GET','POST'])
@login_required
def buyer_cart():
    if current_user.role != 'buyer': return redirect(url_for('dashboard'))
    if request.method == 'POST':
        action     = request.form.get('action')
        product_id = request.form.get('product_id', type=int)
        qty        = request.form.get('qty', 1, type=int)
        if action == 'add':
            existing = query("SELECT * FROM cart_items WHERE user_id=? AND product_id=?",
                             (current_user.id, product_id), one=True)
            if existing:
                query("UPDATE cart_items SET qty=qty+? WHERE user_id=? AND product_id=?",
                      (qty, current_user.id, product_id), commit=True)
            else:
                query("INSERT INTO cart_items (user_id,product_id,qty) VALUES (?,?,?)",
                      (current_user.id, product_id, qty), commit=True)
            flash('Producto añadido al carrito.', 'success')
            return redirect(request.referrer or url_for('buyer_catalogue'))
        elif action == 'remove':
            query("DELETE FROM cart_items WHERE user_id=? AND product_id=?",
                  (current_user.id, product_id), commit=True)
        elif action == 'update':
            if qty < 1:
                query("DELETE FROM cart_items WHERE user_id=? AND product_id=?",
                      (current_user.id, product_id), commit=True)
            else:
                query("UPDATE cart_items SET qty=? WHERE user_id=? AND product_id=?",
                      (qty, current_user.id, product_id), commit=True)
    items = query("""
        SELECT ci.*, p.name, p.price, p.unit, p.image_emoji, p.seller_id,
               u.full_name as seller_name
        FROM cart_items ci
        JOIN products p ON ci.product_id=p.id
        JOIN users u ON p.seller_id=u.id
        WHERE ci.user_id=?
    """, (current_user.id,))
    total = sum(i['price'] * i['qty'] for i in items)
    return render_template('buyer/cart.html', items=items, total=total)

@app.route('/buyer/checkout', methods=['GET','POST'])
@login_required
def buyer_checkout():
    if current_user.role != 'buyer': return redirect(url_for('dashboard'))
    items = query("""
        SELECT ci.*, p.name, p.price, p.unit, p.image_emoji, p.seller_id,
               u.full_name as seller_name
        FROM cart_items ci JOIN products p ON ci.product_id=p.id
        JOIN users u ON p.seller_id=u.id
        WHERE ci.user_id=?
    """, (current_user.id,))
    if not items:
        flash('Tu carrito está vacío.', 'error')
        return redirect(url_for('buyer_cart'))
    total = sum(i['price'] * i['qty'] for i in items)
    if request.method == 'POST':
        address = request.form.get('address','').strip()
        notes   = request.form.get('notes','').strip()
        if not address:
            flash('La dirección de entrega es requerida.', 'error')
            return render_template('buyer/checkout.html', items=items, total=total)
        # Group by seller
        sellers = {}
        for it in items:
            sid = it['seller_id']
            sellers.setdefault(sid, []).append(it)
        for sid, s_items in sellers.items():
            s_total = sum(i['price'] * i['qty'] for i in s_items)
            oid = query(
                "INSERT INTO orders (buyer_id,seller_id,status,total,notes,delivery_address) VALUES (?,?,?,?,?,?)",
                (current_user.id, sid, 'pending', round(s_total,2), notes, address),
                commit=True
            )
            for it in s_items:
                query("INSERT INTO order_items (order_id,product_id,qty,unit_price) VALUES (?,?,?,?)",
                      (oid, it['product_id'], it['qty'], it['price']), commit=True)
            # Notify seller
            seller = query("SELECT * FROM users WHERE id=?", (sid,), one=True)
            query("INSERT INTO notifications (user_id,title,body,type) VALUES (?,?,?,?)",
                  (sid, 'Nuevo pedido recibido',
                   f'{current_user.full_name} realizó un pedido de Bs. {s_total:.2f}.', 'info'),
                  commit=True)
        # Clear cart
        query("DELETE FROM cart_items WHERE user_id=?", (current_user.id,), commit=True)
        flash('¡Pedido realizado exitosamente!', 'success')
        return redirect(url_for('buyer_orders'))
    return render_template('buyer/checkout.html', items=items, total=total)

@app.route('/buyer/orders')
@login_required
def buyer_orders():
    if current_user.role != 'buyer': return redirect(url_for('dashboard'))
    orders = query("""
        SELECT o.*, u.full_name as seller_name, u.company as seller_company
        FROM orders o JOIN users u ON o.seller_id=u.id
        WHERE o.buyer_id=?
        ORDER BY o.created_at DESC
    """, (current_user.id,))
    cart_count = query("SELECT COALESCE(SUM(qty),0) as c FROM cart_items WHERE user_id=?",
                       (current_user.id,), one=True)['c']
    return render_template('buyer/orders.html', orders=orders, cart_count=cart_count)

@app.route('/buyer/orders/<int:oid>')
@login_required
def buyer_order_detail(oid):
    if current_user.role != 'buyer': return redirect(url_for('dashboard'))
    order = query("""
        SELECT o.*, u.full_name as seller_name, u.company as seller_company,
               u.phone as seller_phone
        FROM orders o JOIN users u ON o.seller_id=u.id
        WHERE o.id=? AND o.buyer_id=?
    """, (oid, current_user.id), one=True)
    if not order:
        flash('Pedido no encontrado.', 'error')
        return redirect(url_for('buyer_orders'))
    items = query("""
        SELECT oi.*, p.name, p.image_emoji
        FROM order_items oi JOIN products p ON oi.product_id=p.id
        WHERE oi.order_id=?
    """, (oid,))
    return render_template('buyer/order_detail.html', order=order, items=items)

# ─── SELLER ─────────────────────────────────────────────────────
@app.route('/seller')
@login_required
def seller_home():
    if current_user.role != 'seller': return redirect(url_for('dashboard'))
    orders = query("""
        SELECT o.*, u.full_name as buyer_name, u.company as buyer_company
        FROM orders o JOIN users u ON o.buyer_id=u.id
        WHERE o.seller_id=?
        ORDER BY o.created_at DESC LIMIT 8
    """, (current_user.id,))
    products = query("SELECT * FROM products WHERE seller_id=? ORDER BY name", (current_user.id,))
    stats = {
        'total_products': query("SELECT COUNT(*) as c FROM products WHERE seller_id=?", (current_user.id,), one=True)['c'],
        'total_orders':   query("SELECT COUNT(*) as c FROM orders WHERE seller_id=?", (current_user.id,), one=True)['c'],
        'pending_orders': query("SELECT COUNT(*) as c FROM orders WHERE seller_id=? AND status='pending'", (current_user.id,), one=True)['c'],
        'total_revenue':  query("SELECT COALESCE(SUM(total),0) as s FROM orders WHERE seller_id=? AND status='delivered'", (current_user.id,), one=True)['s'],
    }
    notifs = query("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (current_user.id,))
    return render_template('seller/home.html', orders=orders, products=products,
                           stats=stats, notifs=notifs)

@app.route('/seller/products', methods=['GET','POST'])
@login_required
def seller_products():
    if current_user.role != 'seller': return redirect(url_for('dashboard'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            query("""INSERT INTO products (seller_id,name,description,category,price,unit,stock,min_order,image_emoji)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (current_user.id,
                   request.form['name'], request.form.get('description',''),
                   request.form.get('category','General'),
                   float(request.form['price']),
                   request.form.get('unit','unidad'),
                   int(request.form.get('stock',0)),
                   int(request.form.get('min_order',1)),
                   request.form.get('image_emoji','📦')),
                  commit=True)
            flash('Producto agregado.', 'success')
        elif action == 'delete':
            pid = request.form.get('product_id', type=int)
            query("UPDATE products SET is_active=0 WHERE id=? AND seller_id=?",
                  (pid, current_user.id), commit=True)
            flash('Producto eliminado.', 'info')
        elif action == 'update_stock':
            pid   = request.form.get('product_id', type=int)
            stock = request.form.get('stock', type=int)
            query("UPDATE products SET stock=? WHERE id=? AND seller_id=?",
                  (stock, pid, current_user.id), commit=True)
            flash('Stock actualizado.', 'success')
    products = query("SELECT * FROM products WHERE seller_id=? AND is_active=1 ORDER BY name", (current_user.id,))
    return render_template('seller/products.html', products=products)

@app.route('/seller/orders')
@login_required
def seller_orders():
    if current_user.role != 'seller': return redirect(url_for('dashboard'))
    orders = query("""
        SELECT o.*, u.full_name as buyer_name, u.company as buyer_company, u.phone as buyer_phone
        FROM orders o JOIN users u ON o.buyer_id=u.id
        WHERE o.seller_id=?
        ORDER BY o.created_at DESC
    """, (current_user.id,))
    return render_template('seller/orders.html', orders=orders)

@app.route('/seller/orders/<int:oid>/update', methods=['POST'])
@login_required
def seller_order_update(oid):
    if current_user.role != 'seller': return redirect(url_for('dashboard'))
    status = request.form.get('status')
    valid  = ['confirmed','preparing','in_transit','delivered','cancelled']
    if status in valid:
        query("UPDATE orders SET status=?, updated_at=? WHERE id=? AND seller_id=?",
              (status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), oid, current_user.id),
              commit=True)
        # Notify buyer
        order = query("SELECT * FROM orders WHERE id=?", (oid,), one=True)
        status_labels = {
            'confirmed': 'Confirmado', 'preparing': 'En preparación',
            'in_transit': 'En camino', 'delivered': 'Entregado', 'cancelled': 'Cancelado'
        }
        query("INSERT INTO notifications (user_id,title,body,type) VALUES (?,?,?,?)",
              (order['buyer_id'],
               f'Pedido #{oid} — {status_labels.get(status,status)}',
               f'Tu pedido fue marcado como: {status_labels.get(status,status)}.',
               'success' if status=='delivered' else 'info'),
              commit=True)
        flash(f'Estado actualizado a: {status_labels.get(status,status)}.', 'success')
    return redirect(url_for('seller_orders'))

# ─── TRANSPORTER ────────────────────────────────────────────────
@app.route('/transporter')
@login_required
def transporter_home():
    if current_user.role != 'transporter': return redirect(url_for('dashboard'))
    deliveries = query("""
        SELECT o.*, b.full_name as buyer_name, b.company as buyer_company,
               s.full_name as seller_name, s.company as seller_company
        FROM orders o
        JOIN users b ON o.buyer_id=b.id
        JOIN users s ON o.seller_id=s.id
        WHERE o.status IN ('in_transit','confirmed','preparing')
        ORDER BY o.created_at DESC
    """)
    completed = query("""
        SELECT COUNT(*) as c FROM orders WHERE transporter_id=? AND status='delivered'
    """, (current_user.id,), one=True)['c']
    notifs = query("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 5",
                   (current_user.id,))
    return render_template('transporter/home.html', deliveries=deliveries,
                           completed=completed, notifs=notifs)

@app.route('/transporter/assign/<int:oid>', methods=['POST'])
@login_required
def transporter_assign(oid):
    if current_user.role != 'transporter': return redirect(url_for('dashboard'))
    query("UPDATE orders SET transporter_id=?, status='in_transit', updated_at=? WHERE id=?",
          (current_user.id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), oid), commit=True)
    order = query("SELECT * FROM orders WHERE id=?", (oid,), one=True)
    query("INSERT INTO notifications (user_id,title,body,type) VALUES (?,?,?,?)",
          (order['buyer_id'], f'Pedido #{oid} en camino',
           f'{current_user.full_name} está transportando tu pedido.', 'info'),
          commit=True)
    flash('Entrega asignada a ti.', 'success')
    return redirect(url_for('transporter_home'))

@app.route('/transporter/deliver/<int:oid>', methods=['POST'])
@login_required
def transporter_deliver(oid):
    if current_user.role != 'transporter': return redirect(url_for('dashboard'))
    query("UPDATE orders SET status='delivered', updated_at=? WHERE id=? AND transporter_id=?",
          (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), oid, current_user.id), commit=True)
    order = query("SELECT * FROM orders WHERE id=?", (oid,), one=True)
    query("INSERT INTO notifications (user_id,title,body,type) VALUES (?,?,?,?)",
          (order['buyer_id'], f'Pedido #{oid} entregado ✓',
           'Tu pedido fue entregado exitosamente.', 'success'),
          commit=True)
    flash('Entrega completada.', 'success')
    return redirect(url_for('transporter_home'))

# ─── ADMIN ──────────────────────────────────────────────────────
@app.route('/admin')
@login_required
def admin_home():
    if current_user.role != 'admin': return redirect(url_for('dashboard'))
    users    = query("SELECT * FROM users ORDER BY created_at DESC")
    orders   = query("SELECT o.*, b.full_name as buyer, s.full_name as seller FROM orders o JOIN users b ON o.buyer_id=b.id JOIN users s ON o.seller_id=s.id ORDER BY o.created_at DESC LIMIT 20")
    products = query("SELECT p.*, u.full_name as seller FROM products p JOIN users u ON p.seller_id=u.id WHERE p.is_active=1 ORDER BY p.name")
    stats = {
        'users':    query("SELECT COUNT(*) as c FROM users", one=True)['c'],
        'products': query("SELECT COUNT(*) as c FROM products WHERE is_active=1", one=True)['c'],
        'orders':   query("SELECT COUNT(*) as c FROM orders", one=True)['c'],
        'revenue':  query("SELECT COALESCE(SUM(total),0) as s FROM orders WHERE status='delivered'", one=True)['s'],
    }
    return render_template('admin/home.html', users=users, orders=orders,
                           products=products, stats=stats)

@app.route('/admin/user/<int:uid>/toggle', methods=['POST'])
@login_required
def admin_toggle_user(uid):
    if current_user.role != 'admin': return redirect(url_for('dashboard'))
    query("UPDATE users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?",
          (uid,), commit=True)
    flash('Estado de usuario actualizado.', 'success')
    return redirect(url_for('admin_home'))

# ─── PROFILE ────────────────────────────────────────────────────
@app.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        company   = request.form.get('company','').strip()
        phone     = request.form.get('phone','').strip()
        city      = request.form.get('city','').strip()
        bio       = request.form.get('bio','').strip()
        new_pw    = request.form.get('new_password','')
        if full_name:
            initials = ''.join(w[0].upper() for w in full_name.split()[:2])
            query("UPDATE users SET full_name=?,company=?,phone=?,city=?,bio=?,avatar_initials=? WHERE id=?",
                  (full_name, company, phone, city, bio, initials, current_user.id), commit=True)
        if new_pw and len(new_pw) >= 6:
            query("UPDATE users SET password=? WHERE id=?",
                  (generate_password_hash(new_pw), current_user.id), commit=True)
            flash('Contraseña actualizada.', 'success')
        flash('Perfil actualizado.', 'success')
        return redirect(url_for('profile'))
    row = query("SELECT * FROM users WHERE id=?", (current_user.id,), one=True)
    return render_template('profile.html', user_data=row)

# ─── NOTIFICATIONS ──────────────────────────────────────────────
@app.route('/notifications')
@login_required
def notifications():
    query("UPDATE notifications SET is_read=1 WHERE user_id=?",
          (current_user.id,), commit=True)
    notifs = query("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC",
                   (current_user.id,))
    return render_template('notifications.html', notifs=notifs)

# ─── API helpers ────────────────────────────────────────────────
@app.route('/api/cart/count')
@login_required
def api_cart_count():
    c = query("SELECT COALESCE(SUM(qty),0) as c FROM cart_items WHERE user_id=?",
              (current_user.id,), one=True)['c']
    return jsonify({'count': c})

# ─── Run ────────────────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
