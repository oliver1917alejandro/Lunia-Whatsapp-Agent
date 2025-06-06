#!/bin/bash

# Production deployment script for Lunia WhatsApp Agent
set -e

echo "🚀 Starting Lunia WhatsApp Agent deployment..."

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
DOCKER_COMPOSE_FILE="docker-compose.yml"
APP_NAME="lunia-whatsapp-agent"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    if [ ! -f ".env" ]; then
        print_warning ".env file not found, creating from example..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration"
        else
            print_error ".env.example file not found"
            exit 1
        fi
    fi
    
    print_success "Prerequisites check completed"
}

# Validate environment configuration
validate_config() {
    print_status "Validating configuration..."
    
    # Check required environment variables
    source .env
    
    required_vars=("EVOLUTION_API_URL" "EVOLUTION_API_KEY" "EVOLUTION_INSTANCE_NAME" "OPENAI_API_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        print_error "Please configure these variables in .env file"
        exit 1
    fi
    
    print_success "Configuration validation completed"
}

# Build application
build_app() {
    print_status "Building application..."
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Build the application
    docker-compose build --no-cache
    
    print_success "Application build completed"
}

# Setup SSL certificates (self-signed for development)
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    if [ ! -d "ssl" ]; then
        mkdir -p ssl
    fi
    
    if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
        print_warning "SSL certificates not found, generating self-signed certificates..."
        
        openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        print_warning "Self-signed certificates generated. For production, use proper SSL certificates."
    fi
    
    print_success "SSL setup completed"
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Start only PostgreSQL first
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    sleep 10
    
    # Check if database is accessible
    if docker-compose exec postgres pg_isready -U lunia; then
        print_success "Database initialized successfully"
    else
        print_error "Database initialization failed"
        exit 1
    fi
}

# Start services
start_services() {
    print_status "Starting services..."
    
    if [ "$1" = "--monitoring" ]; then
        print_status "Starting with monitoring services..."
        docker-compose --profile monitoring up -d
    else
        docker-compose up -d
    fi
    
    print_success "Services started"
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Wait for services to start
    sleep 30
    
    # Check application health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Application is healthy"
    else
        print_error "Application health check failed"
        docker-compose logs --tail=50 lunia-whatsapp-agent
        exit 1
    fi
    
    # Check individual services
    if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis is healthy"
    else
        print_warning "Redis health check failed"
    fi
    
    if docker-compose exec postgres pg_isready -U lunia > /dev/null 2>&1; then
        print_success "PostgreSQL is healthy"
    else
        print_warning "PostgreSQL health check failed"
    fi
}

# Show deployment info
show_info() {
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo "📊 Service URLs:"
    echo "  • Application: http://localhost:8000"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Health Check: http://localhost:8000/health"
    echo "  • Metrics: http://localhost:8000/api/metrics"
    echo ""
    echo "🗄️ Database:"
    echo "  • PostgreSQL: localhost:5432"
    echo "  • Redis: localhost:6379"
    echo ""
    echo "🔍 Monitoring (if enabled):"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3000 (admin/admin)"
    echo ""
    echo "📝 Logs:"
    echo "  docker-compose logs -f lunia-whatsapp-agent"
    echo ""
    echo "⛔ Stop services:"
    echo "  docker-compose down"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up deployment artifacts..."
    
    # Stop all services
    docker-compose down --remove-orphans
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    if [ "$1" = "--full" ]; then
        print_warning "Removing all volumes (data will be lost)..."
        docker-compose down -v
        docker volume prune -f
    fi
    
    print_success "Cleanup completed"
}

# Backup function
backup() {
    print_status "Creating backup..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    docker-compose exec postgres pg_dump -U lunia lunia_whatsapp > "$BACKUP_DIR/database.sql"
    
    # Backup configuration
    cp .env "$BACKUP_DIR/"
    cp -r data "$BACKUP_DIR/" 2>/dev/null || true
    cp -r storage "$BACKUP_DIR/" 2>/dev/null || true
    
    print_success "Backup created at $BACKUP_DIR"
}

# Update function
update() {
    print_status "Updating application..."
    
    # Create backup before update
    backup
    
    # Pull latest changes
    git pull origin main
    
    # Rebuild and restart
    build_app
    start_services
    health_check
    
    print_success "Update completed"
}

# Main deployment logic
main() {
    case "$1" in
        "deploy")
            check_prerequisites
            validate_config
            setup_ssl
            build_app
            init_database
            start_services "${@:2}"
            health_check
            show_info
            ;;
        "start")
            start_services "${@:2}"
            ;;
        "stop")
            docker-compose down
            print_success "Services stopped"
            ;;
        "restart")
            docker-compose restart
            print_success "Services restarted"
            ;;
        "status")
            docker-compose ps
            ;;
        "logs")
            docker-compose logs -f "${@:2}"
            ;;
        "cleanup")
            cleanup "${@:2}"
            ;;
        "backup")
            backup
            ;;
        "update")
            update
            ;;
        "health")
            health_check
            ;;
        *)
            echo "Usage: $0 {deploy|start|stop|restart|status|logs|cleanup|backup|update|health}"
            echo ""
            echo "Commands:"
            echo "  deploy        - Full deployment (build, start, health check)"
            echo "  deploy --monitoring - Deploy with monitoring services"
            echo "  start         - Start services"
            echo "  start --monitoring - Start with monitoring"
            echo "  stop          - Stop services"
            echo "  restart       - Restart services"
            echo "  status        - Show service status"
            echo "  logs [service] - Show logs"
            echo "  cleanup       - Clean up deployment"
            echo "  cleanup --full - Clean up including volumes"
            echo "  backup        - Create backup"
            echo "  update        - Update application"
            echo "  health        - Run health check"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
