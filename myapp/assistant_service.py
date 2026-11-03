import re
from typing import Any, Dict, List, Optional
from myapp.models import ErrorCode, FAQ, SupportTicket


class AssistantService:
    """
    Deterministic rule-based assistant intelligence using SQL models
    (FAQ, ErrorCode, and SupportTicket) as the source of truth.
    """

    ERROR_CODE_REGEX = re.compile(r"\b(SW-[A-Z]+-\d{3})\b", re.IGNORECASE)

    # Common stop words to exclude when calculating relevance scores
    STOP_WORDS = {
        "a", "an", "the", "in", "on", "at", "for", "to", "of", "and", "or",
        "is", "are", "was", "were", "be", "been", "how", "what", "where",
        "can", "could", "should", "do", "does", "did", "i", "my", "me", "you",
        "your", "we", "our", "it", "its", "please", "help"
    }

    @classmethod
    def process_message(
        cls,
        user_message: str,
        user=None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Processes a user message and returns a structured response:
        - reply: text message to the user
        - intent: 'error_code' | 'faq' | 'ticket_prompt' | 'ticket_created' | 'general'
        - error_code: str or None
        - faq_id: int or None
        - related_faqs: list of dicts
        - ticket_id: str or None
        - session_updates: dict of state updates to persist
        """
        session_data = session_data or {}
        cleaned_message = user_message.strip()

        if not cleaned_message:
            return {
                "reply": "Hello! I am your SpendWise Assistant. How can I help you manage your finances today?",
                "intent": "general",
                "session_updates": {},
            }

        # 1. Check for Pending Ticket Confirmation
        if session_data.get("awaiting_ticket_confirmation"):
            lower_msg = cleaned_message.lower()
            if any(yes_word in lower_msg for yes_word in ["yes", "yep", "sure", "please", "raise", "create"]):
                # Create the support ticket
                pending_subject = session_data.get(
                    "pending_ticket_subject", "Unresolved Assistant Inquiry"
                )
                pending_desc = session_data.get(
                    "pending_ticket_description", cleaned_message
                )
                related_code = session_data.get("pending_ticket_error_code", "")

                user_instance = user if (user and user.is_authenticated) else None
                contact_email = getattr(user_instance, "email", "")

                ticket = SupportTicket.objects.create(
                    user=user_instance,
                    contact_email=contact_email,
                    subject=pending_subject[:200],
                    description=pending_desc,
                    related_error_code=related_code,
                    priority="MEDIUM",
                    status="OPEN",
                )

                ticket_reply = (
                    f"I have created a support ticket for you!\n\n"
                    f"**Ticket ID:** `{ticket.ticket_id}`\n"
                    f"**Subject:** {ticket.subject}\n"
                    f"**Status:** Open\n\n"
                    f"Our support team has been notified. You can track this ticket anytime under "
                    f"[Support Tickets](/tickets/). Is there anything else I can help you with?"
                )

                return {
                    "reply": ticket_reply,
                    "intent": "ticket_created",
                    "ticket_id": ticket.ticket_id,
                    "session_updates": {
                        "awaiting_ticket_confirmation": False,
                        "pending_ticket_subject": None,
                        "pending_ticket_description": None,
                        "pending_ticket_error_code": None,
                    },
                }
            elif any(no_word in lower_msg for no_word in ["no", "cancel", "nevermind", "stop", "nope"]):
                return {
                    "reply": "No problem! I did not create a ticket. Feel free to ask another question about SpendWise.",
                    "intent": "general",
                    "session_updates": {
                        "awaiting_ticket_confirmation": False,
                        "pending_ticket_subject": None,
                        "pending_ticket_description": None,
                        "pending_ticket_error_code": None,
                    },
                }

        # 2. Check for Error Code Pattern (e.g. SW-AUTH-001)
        error_match = cls.ERROR_CODE_REGEX.search(cleaned_message)
        if error_match:
            raw_code = error_match.group(1).upper()
            error_obj = ErrorCode.objects.filter(
                code__iexact=raw_code, is_active=True
            ).first()

            if error_obj:
                reply = (
                    f"### Error Code: {error_obj.code} — {error_obj.title}\n\n"
                    f"**Severity:** {error_obj.get_severity_display()} | **Category:** {error_obj.category}\n\n"
                    f"**Description:**\n{error_obj.description}\n\n"
                    f"**Possible Causes:**\n{error_obj.possible_causes}\n\n"
                    f"**Recommended Solution:**\n{error_obj.recommended_solution}\n\n"
                    f"If you followed these steps and are still experiencing this issue, "
                    f"reply with 'Raise ticket' and I will create a support ticket for our engineering team."
                )
                return {
                    "reply": reply,
                    "intent": "error_code",
                    "error_code": error_obj.code,
                    "session_updates": {
                        "awaiting_ticket_confirmation": True,
                        "pending_ticket_subject": f"Assistance with error {error_obj.code}: {error_obj.title}",
                        "pending_ticket_description": f"User reported error {error_obj.code} in chat. Original query: {cleaned_message}",
                        "pending_ticket_error_code": error_obj.code,
                    },
                }
            else:
                return {
                    "reply": (
                        f"I could not locate error code `{raw_code}` in the SpendWise error registry. "
                        f"Please verify the code format (e.g. `SW-AUTH-001`, `SW-FORM-001`, `SW-SERVER-001`). "
                        f"Would you like me to raise a support ticket for this issue?"
                    ),
                    "intent": "ticket_prompt",
                    "session_updates": {
                        "awaiting_ticket_confirmation": True,
                        "pending_ticket_subject": f"Unknown error code inquiry: {raw_code}",
                        "pending_ticket_description": cleaned_message,
                        "pending_ticket_error_code": raw_code,
                    },
                }

        # 3. Search SQL FAQs by relevance scoring
        best_faq, score, related = cls.search_faqs(cleaned_message)

        if best_faq and score >= 2:
            reply = f"**{best_faq.question}**\n\n{best_faq.answer}"

            related_payload = []
            if related:
                reply += "\n\n**Related Help Topics:**"
                for r in related:
                    reply += f"\n- {r.question}"
                    related_payload.append({
                        "id": r.id,
                        "question": r.question,
                        "category": r.category,
                    })

            return {
                "reply": reply,
                "intent": "faq",
                "faq_id": best_faq.id,
                "related_faqs": related_payload,
                "session_updates": {
                    "awaiting_ticket_confirmation": False,
                },
            }

        # 4. Unknown Question Fallback: Offer to create a Support Ticket
        fallback_reply = (
            "I couldn't find an exact answer to that question in the SpendWise knowledge base.\n\n"
            "Would you like me to raise a support ticket for our support team to look into this? "
            "(Reply **'Yes'** to raise a ticket, or feel free to rephrase your question)."
        )

        return {
            "reply": fallback_reply,
            "intent": "ticket_prompt",
            "session_updates": {
                "awaiting_ticket_confirmation": True,
                "pending_ticket_subject": f"User question: {cleaned_message[:60]}...",
                "pending_ticket_description": cleaned_message,
                "pending_ticket_error_code": "",
            },
        }

    @classmethod
    def search_faqs(cls, query: str):
        """
        Tokenizes the query and scores active FAQs based on:
        - Exact question match (score: 10)
        - Words in question (score: 3 per word)
        - Words in category (score: 2 per word)
        - Words in answer (score: 1 per word)
        Returns: (best_faq, highest_score, [related_faqs])
        """
        faqs = FAQ.objects.filter(is_active=True)
        if not faqs.exists():
            return None, 0, []

        query_clean = query.lower()
        query_words = set(
            re.findall(r"\w+", query_clean)
        ) - cls.STOP_WORDS

        if not query_words:
            # Query only had stop words, match first 3 general faqs
            return faqs.first(), 1, list(faqs[1:3])

        scored_faqs = []

        for faq in faqs:
            score = 0
            q_lower = faq.question.lower()
            a_lower = faq.answer.lower()
            c_lower = faq.category.lower()

            # Exact question match
            if query_clean in q_lower or q_lower in query_clean:
                score += 10

            for word in query_words:
                if word in q_lower:
                    score += 3
                if word in c_lower:
                    score += 2
                if word in a_lower:
                    score += 1

            if score > 0:
                scored_faqs.append((faq, score))

        if not scored_faqs:
            return None, 0, []

        scored_faqs.sort(key=lambda item: item[1], reverse=True)
        best_faq, best_score = scored_faqs[0]

        # Related FAQs with next best scores
        related = [f for f, s in scored_faqs[1:4] if s >= 2]

        return best_faq, best_score, related
