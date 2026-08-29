# LeadFlow – EdTech Lead Management CRM

A full-stack Customer Relationship Management (CRM) application designed for managing prospective learners and tracking the sales pipeline of an EdTech business.

## 📌 Project Overview

LeadFlow helps sales teams manage learner leads from the initial enquiry through follow-ups and conversion.

The application provides a centralized system to add, manage, search, filter, and track leads while automatically calculating lead scores and displaying sales metrics through a dashboard.

## ✨ Features

- 📊 Sales dashboard with key CRM metrics
- 👤 Add new learner leads
- ✏️ Edit existing leads
- 🗑️ Delete leads
- 🔎 Search leads by name, phone, or email
- 🔽 Filter leads by status
- 📚 Track interested courses
- 📢 Track lead sources
- 📅 Manage follow-up dates
- 📝 Store learner notes
- 🎯 Automatic lead scoring
- 🔥 Lead categorization as Hot, Warm, or Cold
- 📈 Lead pipeline tracking
- 💰 Conversion-rate calculation
- 💾 SQLite database for persistent data storage
- 📱 Responsive and clean user interface

## 🛠️ Tech Stack

### Backend
- Python
- Flask
- SQLite

### Frontend
- HTML5
- CSS3
- Jinja2 Templates

### Development Tools
- Visual Studio Code
- Git
- GitHub

## 📂 Project Structure

```text
edtech-lead-crm/
│
├── app.py
├── crm.db
├── requirements.txt
├── README.md
│
├── static/
│   └── style.css
│
└── templates/
    ├── base.html
    ├── dashboard.html
    └── leads.html