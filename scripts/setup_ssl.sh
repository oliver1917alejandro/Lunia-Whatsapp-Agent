#!/bin/bash
# SSL Certificate Setup Script for Lunia WhatsApp Agent

set -e

echo "🔒 SSL Certificate Setup for Lunia WhatsApp Agent"
echo "================================================="

# Configuration
DOMAIN=${1:-"localhost"}
SSL_DIR="./ssl"
CERT_PATH="$SSL_DIR/cert.pem"
KEY_PATH="$SSL_DIR/key.pem"
NGINX_SSL_DIR="./nginx/ssl"

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"
mkdir -p "$NGINX_SSL_DIR"

echo "📍 Domain: $DOMAIN"
echo "📂 SSL Directory: $SSL_DIR"

# Function to generate self-signed certificate
generate_self_signed() {
    echo "🔧 Generating self-signed certificate..."
    
    openssl req -x509 -newkey rsa:4096 -keyout "$KEY_PATH" -out "$CERT_PATH" \
        -days 365 -nodes -subj "/CN=$DOMAIN"
    
    echo "✅ Self-signed certificate generated"
}

# Function to setup Let's Encrypt certificate
setup_letsencrypt() {
    echo "🌐 Setting up Let's Encrypt certificate..."
    
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        echo "❌ Certbot not found. Installing..."
        
        # Install certbot based on OS
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y certbot
            elif command -v yum &> /dev/null; then
                sudo yum install -y certbot
            else
                echo "❌ Unable to install certbot automatically. Please install it manually."
                exit 1
            fi
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                brew install certbot
            else
                echo "❌ Homebrew not found. Please install certbot manually."
                exit 1
            fi
        else
            echo "❌ Unsupported OS for automatic certbot installation."
            exit 1
        fi
    fi
    
    echo "📋 Obtaining Let's Encrypt certificate for $DOMAIN..."
    echo "⚠️  Make sure your domain points to this server and port 80 is accessible."
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Stop nginx if running
        docker-compose stop nginx 2>/dev/null || true
        
        # Obtain certificate
        sudo certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos \
            --email "admin@$DOMAIN"
        
        # Copy certificates to our SSL directory
        sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$CERT_PATH"
        sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$KEY_PATH"
        
        # Set proper permissions
        sudo chown $(whoami):$(whoami) "$CERT_PATH" "$KEY_PATH"
        chmod 644 "$CERT_PATH"
        chmod 600 "$KEY_PATH"
        
        echo "✅ Let's Encrypt certificate obtained and configured"
    else
        echo "❌ Let's Encrypt setup cancelled"
        exit 1
    fi
}

# Function to copy certificates to nginx directory
copy_to_nginx() {
    echo "📋 Copying certificates to nginx directory..."
    cp "$CERT_PATH" "$NGINX_SSL_DIR/"
    cp "$KEY_PATH" "$NGINX_SSL_DIR/"
    echo "✅ Certificates copied to nginx directory"
}

# Function to update environment file
update_env_file() {
    ENV_FILE="./deploy/.env.production"
    
    if [[ -f "$ENV_FILE" ]]; then
        echo "📝 Updating environment file..."
        
        # Update SSL paths in environment file
        sed -i.bak "s|ENABLE_HTTPS=.*|ENABLE_HTTPS=true|g" "$ENV_FILE"
        sed -i.bak "s|SSL_CERT_PATH=.*|SSL_CERT_PATH=/etc/nginx/ssl/cert.pem|g" "$ENV_FILE"
        sed -i.bak "s|SSL_KEY_PATH=.*|SSL_KEY_PATH=/etc/nginx/ssl/key.pem|g" "$ENV_FILE"
        
        echo "✅ Environment file updated"
    else
        echo "⚠️  Environment file not found at $ENV_FILE"
    fi
}

# Function to verify certificates
verify_certificates() {
    echo "🔍 Verifying certificates..."
    
    if [[ -f "$CERT_PATH" && -f "$KEY_PATH" ]]; then
        # Check certificate validity
        if openssl x509 -in "$CERT_PATH" -text -noout >/dev/null 2>&1; then
            echo "✅ Certificate is valid"
            
            # Show certificate details
            echo "📋 Certificate details:"
            openssl x509 -in "$CERT_PATH" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)"
        else
            echo "❌ Certificate is invalid"
            exit 1
        fi
        
        # Check private key
        if openssl rsa -in "$KEY_PATH" -check -noout >/dev/null 2>&1; then
            echo "✅ Private key is valid"
        else
            echo "❌ Private key is invalid"
            exit 1
        fi
        
        # Check if certificate and key match
        cert_modulus=$(openssl x509 -noout -modulus -in "$CERT_PATH" | openssl md5)
        key_modulus=$(openssl rsa -noout -modulus -in "$KEY_PATH" | openssl md5)
        
        if [[ "$cert_modulus" == "$key_modulus" ]]; then
            echo "✅ Certificate and private key match"
        else
            echo "❌ Certificate and private key do not match"
            exit 1
        fi
    else
        echo "❌ Certificate files not found"
        exit 1
    fi
}

# Main menu
echo "Choose SSL setup option:"
echo "1) Generate self-signed certificate (for development/testing)"
echo "2) Setup Let's Encrypt certificate (for production)"
echo "3) Verify existing certificates"
echo "4) Exit"

read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        generate_self_signed
        copy_to_nginx
        update_env_file
        verify_certificates
        echo "🎉 Self-signed SSL certificate setup complete!"
        ;;
    2)
        if [[ "$DOMAIN" == "localhost" ]]; then
            read -p "Enter your domain name: " DOMAIN
        fi
        setup_letsencrypt
        copy_to_nginx
        update_env_file
        verify_certificates
        echo "🎉 Let's Encrypt SSL certificate setup complete!"
        ;;
    3)
        verify_certificates
        ;;
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📋 Next steps:"
echo "1. Update your DNS records to point to this server"
echo "2. Make sure ports 80 and 443 are open"
echo "3. Start the application with: ./deploy/deploy.sh start"
echo "4. Access your application at: https://$DOMAIN"
echo ""
echo "🔄 To renew Let's Encrypt certificates, run: certbot renew"
