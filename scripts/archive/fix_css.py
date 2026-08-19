import os
import re

file_path = r"d:\FixLink-V1\app\templates\login.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_css = """<style>
    /* ====================================================
       LIGHT MODE (Default fallback)
       ==================================================== */
    .bg-orb-top-right, .bg-orb-bottom-left {
        display: none;
    }
    .glass-login-card {
        width: 100%;
        max-width: 460px;
        padding: 40px 36px;
        background: #ffffff;
        border: none;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        z-index: 1;
        position: relative;
    }
    .glass-login-card .form-logo {
        max-width: 140px;
        margin: 0 auto 24px auto;
        display: block;
    }
    .glass-login-card h3 {
        font-size: 26px;
        font-weight: 700;
        color: #212529;
        text-align: left;
        margin: 0 0 6px 0;
    }
    .glass-login-card .subtext {
        font-size: 14px;
        color: #6c757d;
        text-align: left;
        margin: 0 0 24px 0;
    }
    .glass-login-card .form-label {
        font-size: 13px;
        font-weight: 500;
        color: #212529;
        margin: 0 0 6px 0;
        display: block;
    }
    .glass-login-card .text-danger { color: #dc3545 !important; }
    .glass-login-card .form-control {
        width: 100%;
        height: 46px;
        border-radius: 8px;
        background: #ffffff !important;
        border: 1px solid #ced4da !important;
        color: #212529 !important;
        font-size: 14px;
        padding: 0 14px;
        box-shadow: none !important;
        transition: all 0.2s ease;
    }
    .glass-login-card .form-control::placeholder { color: #adb5bd !important; }
    .glass-login-card .form-control:focus {
        border-color: #86b7fe !important;
        box-shadow: 0 0 0 0.25rem rgba(13,110,253,.25) !important;
    }
    .glass-login-card .field-group { margin-bottom: 14px; }
    .glass-login-card .pwd-wrapper { position: relative; display: block; width: 100%; }
    .glass-login-card .btn-eye {
        position: absolute;
        right: 14px;
        top: 50%;
        transform: translateY(-50%);
        background: none;
        border: none;
        color: #6c757d;
        padding: 0;
        z-index: 10;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
    }
    .glass-login-card .btn-eye:hover { color: #212529; }
    .glass-login-card .forgot-pwd {
        display: block;
        text-align: left;
        font-size: 13px;
        color: #6c757d;
        text-decoration: none;
        margin-top: 6px;
        margin-bottom: 20px;
    }
    .glass-login-card .forgot-pwd:hover { color: #0b4d8c; text-decoration: underline; }
    .glass-login-card .btn-primary {
        width: 100%;
        height: 46px;
        border-radius: 8px;
        background: #0b4d8c !important;
        border: 1px solid #0b4d8c !important;
        color: #ffffff !important;
        font-size: 15px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .glass-login-card .btn-primary:hover {
        background: #083968 !important;
        border-color: #083968 !important;
    }
    .glass-login-card .footer-links {
        margin-top: 24px;
        text-align: left;
        font-size: 14px;
        display: flex;
        justify-content: flex-start;
        gap: 6px;
    }
    .glass-login-card .footer-text { color: #6c757d; }
    .glass-login-card .footer-link { color: #0b4d8c; font-weight: 600; text-decoration: none; }
    .glass-login-card .footer-link:hover { text-decoration: underline; }
    
    .glass-login-card .pro-link-group {
        margin-top: 12px;
        text-align: left;
        font-size: 13px;
        padding-top: 16px;
        border-top: 1px solid #e9ecef;
    }
    .glass-login-card .pro-text { color: #6c757d; }
    .glass-login-card .pro-highlight { color: #212529; font-weight: 600; }
    .glass-login-card .pro-link { color: #0b4d8c; font-weight: 600; text-decoration: none; }
    
    .glass-login-card .alert { font-size: 14px; border-radius: 8px; margin-bottom: 20px; }

    /* Hide the extra container from base.html to prevent spacing issues */
    .main-content > .container.mt-3 {
        position: absolute;
        top: 20px;
        left: 0;
        right: 0;
        z-index: 10;
        width: 100%;
        max-width: 460px;
        margin: 0 auto !important;
    }

    /* ====================================================
       DARK MODE (Glassy Monochrome)
       ==================================================== */
    body[data-theme="dark"] {
        background-color: #080808 !important;
        background-image: url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noiseFilter%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.65%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noiseFilter)%22 opacity=%220.02%22/%3E%3C/svg%3E') !important;
        color: #ffffff;
        overflow: hidden !important;
    }
    
    body[data-theme="dark"] .vyas-navbar {
        background: rgba(255,255,255,0.03) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-bottom: 1px solid rgba(255,255,255,0.07) !important;
        box-shadow: none !important;
    }
    body[data-theme="dark"] .vyas-navbar .nav-link,
    body[data-theme="dark"] .vyas-navbar .navbar-brand .brand-text,
    body[data-theme="dark"] .vyas-navbar .navbar-brand .brand-subtitle,
    body[data-theme="dark"] .vyas-navbar .bi {
        color: rgba(255,255,255,0.75) !important;
    }
    body[data-theme="dark"] .vyas-navbar .nav-link:hover,
    body[data-theme="dark"] .vyas-navbar .nav-link:hover .bi,
    body[data-theme="dark"] .vyas-navbar .navbar-brand:hover .brand-text,
    body[data-theme="dark"] .vyas-navbar button:hover .bi {
        color: #ffffff !important;
    }
    
    body[data-theme="dark"] .bg-orb-top-right {
        display: block;
        position: fixed;
        top: -10%;
        left: 50%;
        transform: translateX(15%);
        width: 700px;
        height: 700px;
        background: rgba(255, 255, 255, 0.18);
        filter: blur(120px);
        border-radius: 50%;
        pointer-events: none;
        z-index: 0;
    }
    
    body[data-theme="dark"] .bg-orb-bottom-left {
        display: block;
        position: fixed;
        bottom: -20%;
        right: 50%;
        transform: translateX(-15%);
        width: 500px;
        height: 500px;
        background: rgba(255, 255, 255, 0.12);
        filter: blur(100px);
        border-radius: 50%;
        pointer-events: none;
        z-index: 0;
    }

    body[data-theme="dark"] .glass-login-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 20px;
        backdrop-filter: blur(24px) saturate(140%);
        -webkit-backdrop-filter: blur(24px) saturate(140%);
        box-shadow: 0 0 0 1px rgba(255,255,255,0.05);
    }
    body[data-theme="dark"] .glass-login-card .form-logo { opacity: 0.85; }
    body[data-theme="dark"] .glass-login-card h3 { color: #ffffff; }
    body[data-theme="dark"] .glass-login-card .subtext { color: rgba(255,255,255,0.4); }
    body[data-theme="dark"] .glass-login-card .form-label { color: rgba(255,255,255,0.6); }
    body[data-theme="dark"] .glass-login-card .text-danger { color: rgba(255,100,100,0.8) !important; }

    body[data-theme="dark"] .glass-login-card .form-control {
        border-radius: 10px;
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #ffffff !important;
    }
    body[data-theme="dark"] .glass-login-card .form-control::placeholder { color: rgba(255,255,255,0.3) !important; }
    body[data-theme="dark"] .glass-login-card .form-control:focus {
        border-color: rgba(255,255,255,0.3) !important;
        background: rgba(255,255,255,0.1) !important;
    }
    body[data-theme="dark"] .glass-login-card .btn-eye { color: rgba(255,255,255,0.4); }
    body[data-theme="dark"] .glass-login-card .btn-eye:hover { color: #ffffff; }
    body[data-theme="dark"] .glass-login-card .forgot-pwd { color: rgba(255,255,255,0.4); }
    body[data-theme="dark"] .glass-login-card .forgot-pwd:hover { color: #ffffff; }

    body[data-theme="dark"] .glass-login-card .btn-primary {
        border-radius: 10px;
        background: rgba(255,255,255,0.13) !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        color: #ffffff !important;
    }
    body[data-theme="dark"] .glass-login-card .btn-primary:hover {
        background: rgba(255,255,255,0.2) !important;
        border-color: rgba(255,255,255,0.28) !important;
    }
    body[data-theme="dark"] .glass-login-card .btn-primary:active { transform: scale(0.98); }

    body[data-theme="dark"] .glass-login-card .footer-text { color: rgba(255,255,255,0.4); }
    body[data-theme="dark"] .glass-login-card .footer-link { color: #ffffff; }
    body[data-theme="dark"] .glass-login-card .pro-link-group { border-top: 1px solid rgba(255,255,255,0.05); }
    body[data-theme="dark"] .glass-login-card .pro-text { color: rgba(255,255,255,0.4); }
    body[data-theme="dark"] .glass-login-card .pro-highlight { color: rgba(255,255,255,0.85); }
    body[data-theme="dark"] .glass-login-card .pro-link { color: rgba(255,255,255,0.85); }
    
    body[data-theme="dark"] .glass-login-card .alert {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        color: #fff;
        backdrop-filter: blur(10px);
    }
    body[data-theme="dark"] .glass-login-card .alert-danger {
        border-color: rgba(255,100,100,0.3);
        background: rgba(255,100,100,0.05);
    }
    body[data-theme="dark"] .glass-login-card .btn-close {
        filter: invert(1) grayscale(100%) brightness(200%);
    }
</style>"""

pattern = re.compile(r"<style>.*?</style>", re.DOTALL)
new_content = pattern.sub(new_css, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Updated successfully")
