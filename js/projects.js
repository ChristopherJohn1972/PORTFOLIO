/* ============================================
   PROJECT DATA
   ============================================
   Add or update projects here. The portfolio
   reads this data to display project cards.

   URLs are NOT exposed in the frontend.
   Visitors must request project links through
   the contact system.
   ============================================ */

const FEATURED_PROJECTS = [
    {
        name: "CRM V2 — Fullstack CRM & Business Management Platform",
        description: "A fullstack CRM and business-management platform supporting customer management, sales, financial operations, authentication, reporting, and accounting workflows.",
        status: "Live",
        technologies: ["Python", "Django REST Framework", "JavaScript", "React", "SQL", "MySQL", "PostgreSQL", "REST APIs", "JWT", "Git"],
        features: [
            "Client, Company & Contact Management",
            "Leads & Deal Workflows",
            "Invoice & Customer Numbering",
            "Payments: M-Pesa, PayPal, Stripe Sandbox",
            "Revenue, Profit & Outstanding Balances",
            "Accounts Receivable & Payable",
            "Financial Reporting & Workflows",
            "JWT Authentication & RBAC",
            "Roles, Permissions & Protected Workflows",
            "Relational Database Design & Migrations",
            "React Frontend Integrated with Backend APIs",
            "Cloud Deployment & Production Configuration"
        ],
        category: "fullstack",
        featured: true
    },
    {
        name: "Rental Management Services",
        description: "A rental management platform supporting tenants, staff, administrators, property operations, maintenance, payments, and receipts.",
        status: "Live",
        technologies: ["Python", "FastAPI", "Firebase", "JavaScript", "REST APIs", "Docker", "Cloud Deployment"],
        features: [
            "Tenant, Staff & Administrator Workflows",
            "Property Operations Management",
            "Maintenance Requests with Photo Handling",
            "Receipt & Payment Workflows",
            "M-Pesa & PayPal Payment Integration",
            "Firebase Realtime Database",
            "Frontend/Backend Communication",
            "API, Database & Deployment Troubleshooting",
            "Docker & Cloud Deployment"
        ],
        category: "fullstack",
        featured: true
    }
];
