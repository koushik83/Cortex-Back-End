# Simple Company Chatbot

A lightweight, embeddable chatbot that can be integrated into any website with a single line of code. The chatbot processes company documents (PDFs, Word files, Excel, etc.) and uses them to provide relevant responses to customer queries.

## Features

- 🚀 Single-line website integration
- 📄 Support for multiple document types (PDF, DOCX, XLSX, TXT)
- 💬 Real-time chat interface
- 📱 Mobile-responsive design
- 📊 Basic analytics and insights
- 🔄 Webhook support for company feedback

## Quick Start

### 1. Add to Your Website

```html
<script src="https://yourbot.com/bot.js" data-company="YOUR_COMPANY_ID"></script>
```

### 2. Upload Your Documents

Use the setup endpoint to upload your company documents:

```bash
curl -X POST https://yourbot.com/setup/YOUR_COMPANY_ID \
  -F "files=@document1.pdf" \
  -F "files=@document2.docx"
```

## Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/yourusername/simple-bot.git
cd simple-bot
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
simple-bot/
├── app/
│   ├── main.py           # FastAPI app + routes
│   ├── bot.py            # Core chatbot logic
│   ├── processor.py      # Document processing
│   ├── insights.py       # Analytics
│   └── store.py          # Data storage
├── static/
│   ├── bot.js            # Widget script
│   └── style.css         # Widget styles
├── templates/
│   └── widget.html       # Widget template
└── requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file:

```env
SERVER_URL=https://yourbot.com
DEBUG=True
MAX_DOCUMENT_SIZE=10485760  # 10MB
```

### Webhook Setup

Configure webhook URL for company feedback:

```bash
curl -X POST https://yourbot.com/setup/webhook \
  -H "Content-Type: application/json" \
  -d '{"company_id": "YOUR_COMPANY_ID", "webhook_url": "https://your-company.com/webhook"}'
```

## API Endpoints

### Setup
- `POST /setup/{company_id}` - Upload company documents
- `POST /setup/webhook` - Configure webhook

### Chat
- `POST /chat` - Send message to chatbot
- `GET /analytics/{company_id}` - Get chat analytics

## Customization

### Widget Appearance

Modify widget appearance by overriding CSS variables:

```css
:root {
    --chat-primary-color: #2196F3;
    --chat-text-color: #333;
    --chat-bg-color: white;
}
```

### Custom Welcome Message

Edit in widget.html:

```html
<div class="message bot-message">
    Your custom welcome message here
</div>
```

## Analytics

The system provides basic analytics including:
- Total conversations
- Common questions
- Response confidence scores
- User satisfaction metrics

Access analytics via the dashboard or API endpoint.

## Development

### Adding New Document Types

1. Add handler in processor.py:
```python
def process_new_type(content):
    # Process new document type
    pass
```

2. Register in supported types:
```python
supported_types = [..., '.newtype']
```

### Testing

Run tests:
```bash
pytest tests/
```

## Security

- All document processing is done server-side
- Data is stored securely
- No sensitive information is exposed to the client
- CORS configured for widget compatibility

## Limitations

- Maximum document size: 10MB
- Supported file types: PDF, DOCX, XLSX, TXT
- Rate limiting: 100 requests per minute per company

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Create pull request

## License

MIT License - see LICENSE file for details

## Support

For support, email support@yourbot.com or create an issue in the repository.