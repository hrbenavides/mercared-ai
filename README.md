# 🛒 MercaRed AI

**Ecosistema digital de abastecimiento B2B** para pequeños comercios, distribuidores y transportistas.

[![Demo en vivo](https://img.shields.io/badge/Demo-En%20vivo-brightgreen)](https://mercared-ai.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey)](https://flask.palletsprojects.com/)

---

## 🌐 Demo en vivo

Puedes probar la aplicación directamente desde tu navegador:

👉 **[https://mercared-ai.onrender.com](https://mercared-ai.onrender.com)**

> **Nota:** El plan gratuito de Render "duerme" la aplicación tras 15 minutos de inactividad. La primera visita puede tardar unos segundos en cargar mientras el servidor se reactiva.

---

## ✨ Características

- **Roles diferenciados**: Comprador, Vendedor, Transportista y Administrador.
- **Catálogo de productos** con carrito de compras.
- **Gestión de pedidos** con seguimiento de estado (pendiente → confirmado → preparando → en camino → entregado).
- **Notificaciones** en tiempo real para cada usuario.
- **Dashboard personalizado** según el rol.
- **Sistema de autenticación** con Flask-Login.
- **Diseño responsive** adaptable a móviles y escritorio.

---

## 🛠️ Tecnologías

| Capa | Tecnología |
|------|------------|
| Backend | Flask (Python) |
| Base de datos | SQLite |
| Frontend | HTML + CSS (Jinja2) |
| Autenticación | Flask-Login |
| Servidor de producción | Gunicorn |
| Despliegue | Render |

---

## 🚀 Cómo ejecutar localmente

### Requisitos previos

- Python 3.9 o superior
- Git (opcional)

### Pasos

1. **Clona el repositorio:**

   ```bash
   git clone https://github.com/hrbenavides/mercared-ai.git
   cd mercared-ai
   ```

2. **Ejecuta el script de inicio** (instala dependencias y crea la base de datos automáticamente):

   ```bash
   python start.py
   ```

3. **Abre tu navegador en:**

   ```
   http://127.0.0.1:5000
   ```

### Alternativa manual

Si prefieres hacerlo paso a paso:

```bash
pip install -r requirements.txt
python app.py
```

---

## 🔑 Cuentas de prueba

| Rol | Correo | Contraseña |
|-----|--------|------------|
| 🏪 Comprador | `comprador@demo.bo` | `demo123` |
| 🏭 Vendedor | `vendedor@demo.bo` | `demo123` |
| 🚚 Transportista | `transporte@demo.bo` | `demo123` |
| ⚙️ Administrador | `admin@mercared.bo` | `admin123` |

---

## 📁 Estructura del proyecto

```
mercared/
├── app.py              # Backend (Flask + SQLite)
├── start.py            # Script de inicio rápido
├── requirements.txt    # Dependencias del proyecto
├── mercared.db         # Base de datos (se crea automáticamente)
└── templates/
    ├── base.html       # Layout con sidebar
    ├── landing.html    # Página principal
    ├── login.html      # Inicio de sesión
    ├── register.html   # Registro
    ├── profile.html    # Perfil de usuario
    ├── notifications.html
    ├── buyer/          # Vistas del comprador
    ├── seller/         # Vistas del distribuidor
    ├── transporter/    # Vistas del transportista
    └── admin/          # Panel de administración
```

---

## 🔄 Flujo de un pedido

```
Comprador realiza pedido
        ↓
Vendedor confirma y prepara
        ↓
Transportista se asigna y recoge
        ↓
Comprador recibe y confirma entrega
```

Cada cambio de estado genera una **notificación automática** al comprador.

---

## 📝 Licencia

Este proyecto está bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

## 👨‍💻 Autor

**Henry Benavides**

- GitHub: [@hrbenavides](https://github.com/hrbenavides)
- Proyecto desarrollado como parte del curso de Ingeniería Electrónica — UMSA

---

<p align="center">
  Hecho con ❤️ en Bolivia 🇧🇴
</p>
