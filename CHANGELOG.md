# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Planned for v1.0.0
- REST API endpoints for subscription management
- Advanced automation and dunning management
- Performance optimizations and caching
- Final security audit

## [0.1.2] - 2026-08-31

### Fixed
- Fixed all GitHub URLs pointing to wrong repository (was `wagtail-subscriptions/wagtail-subscriptions`, now `mojnomiya/wagtail_subscriptions`)
- Fixed placeholder `yourusername` in support links
- Added Django Packages badge to README

## [0.1.1] - 2026-02-10

### Added
- Initial release of wagtail-subscriptions
- Complete subscription management system for Wagtail CMS
- Multiple payment processor support (Stripe, Paddle, PayPal)
- Feature-based access control system
- Modern admin dashboard with Wagtail integration
- Responsive pricing table components
- Customer portal and billing management
- Template tags for easy integration
- Permission decorators and mixins
- Management commands for setup
- Comprehensive documentation

### Features
- **Subscription Plans**: Flexible billing periods, trial support, plan upgrades
- **Feature Management**: Modular features with quota support
- **Payment Integration**: Stripe (built-in), Paddle, PayPal support
- **Admin Interface**: Beautiful Wagtail-integrated dashboard
- **Frontend Components**: Modern UI with Tailwind CSS
- **Permission System**: View-level and template-level access control
- **Analytics**: Basic subscription metrics and reporting
- **Customer Management**: Extended customer profiles and billing info

### Technical
- Django 3.2+ support
- Wagtail 4.0+ support
- Python 3.8+ support
- Comprehensive test coverage
- Type hints throughout codebase
- Internationalization support