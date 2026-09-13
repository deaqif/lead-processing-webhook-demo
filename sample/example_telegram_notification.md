# Sample Telegram Alert Output

When an inbound lead is submitted, the Telegram notification service generates and dispatches the following markdown message to the designated Telegram chat/channel:

```markdown
🚀 *NEW INBOUND LEAD RECEIVED*
━━━━━━━━━━━━━━━━━━━━━━
📋 *Form:* `Enterprise Automation Inquiry`
🆔 *Lead ID:* `LD-20260913-F3-E1428`
👤 *Name:* Tariq Mansor
📧 *Email:* tariq.mansor@novatech.my
📱 *Phone:* +60139982145
🏢 *Company:* NovaTech Solutions Sdn Bhd
🎯 *Interest:* Workflow & API Automation
💰 *Budget:* RM 15,000 - RM 30,000
📊 *Campaign:* `google_search` / `b2b_lead_gen_q3`
━━━━━━━━━━━━━━━━━━━━━━
💬 *Inquiry Message:*
_We need to connect our web lead intake directly to Google Sheets and receive instant alerts on our private operations Telegram channel._
━━━━━━━━━━━━━━━━━━━━━━
🕒 _2026-09-13 13:30:00 UTC_
```

### Key Business Benefits of this Alert:
1. **Immediate Lead Response Time:** Sales engineers receive sub-second alerts right on their phones, drastically cutting lead response time from hours to under 2 minutes.
2. **Context-Rich:** Contains UTM attribution, budget, and project requirements directly in the chat preview.
3. **Audit Tracking:** Includes the unified `Lead ID` for reference across SQLite and Google Sheets.
