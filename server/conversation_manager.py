import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from tinydb import TinyDB, Query
from pathlib import Path
import uuid

class ConversationManager:
    """Manages chat conversations with TinyDB persistence"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent / "conversations.json"
        
        self.db = TinyDB(db_path)
        self.conversations_table = self.db.table('conversations')
        self.messages_table = self.db.table('messages')
        
    def create_conversation(self, title: str = None) -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        conversation = {
            'id': conversation_id,
            'title': title or "New Chat",
            'created_at': timestamp,
            'last_interacted': timestamp,
            'message_count': 0
        }
        
        self.conversations_table.insert(conversation)
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a single conversation with its messages"""
        Conversation = Query()
        conversation = self.conversations_table.search(Conversation.id == conversation_id)
        
        if not conversation:
            return None
            
        conversation = conversation[0]
        
        # Get messages for this conversation
        Message = Query()
        messages = self.messages_table.search(Message.conversation_id == conversation_id)
        
        # Sort messages by timestamp
        messages.sort(key=lambda x: x.get('timestamp', ''))
        
        return {
            'id': conversation['id'],
            'title': conversation['title'],
            'created_at': conversation['created_at'],
            'last_interacted': conversation['last_interacted'],
            'message_count': conversation['message_count'],
            'messages': messages
        }
    
    def get_all_conversations(self) -> List[Dict]:
        """Get all conversations (without messages) sorted by last_interacted"""
        conversations = self.conversations_table.all()
        
        # Sort by last_interacted (most recent first)
        conversations.sort(key=lambda x: x.get('last_interacted', ''), reverse=True)
        
        return conversations
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   message_type: str = 'text', metadata: Dict = None) -> bool:
        """Add a message to a conversation"""
        Conversation = Query()
        conversation = self.conversations_table.search(Conversation.id == conversation_id)
        
        if not conversation:
            return False
        
        timestamp = datetime.now().isoformat()
        message_id = str(uuid.uuid4())
        
        message = {
            'id': message_id,
            'conversation_id': conversation_id,
            'role': role,  # 'user', 'assistant', 'error'
            'content': content,
            'type': message_type,  # 'text', 'plan', 'execution_result', 'chat', etc.
            'timestamp': timestamp,
            'metadata': metadata or {}
        }
        
        # Insert message
        self.messages_table.insert(message)
        
        # Update conversation last_interacted and message_count
        conversation_data = conversation[0]
        new_count = conversation_data.get('message_count', 0) + 1
        
        self.conversations_table.update({
            'last_interacted': timestamp,
            'message_count': new_count
        }, Conversation.id == conversation_id)
        
        return True
    
    def update_conversation_title(self, conversation_id: str, title: str) -> bool:
        """Update the title of a conversation"""
        Conversation = Query()
        conversation = self.conversations_table.search(Conversation.id == conversation_id)
        
        if not conversation:
            return False
        
        self.conversations_table.update({
            'title': title,
            'last_interacted': datetime.now().isoformat()
        }, Conversation.id == conversation_id)
        
        return True
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages"""
        Conversation = Query()
        Message = Query()
        
        # Check if conversation exists
        conversation = self.conversations_table.search(Conversation.id == conversation_id)
        if not conversation:
            return False
        
        # Delete all messages
        self.messages_table.remove(Message.conversation_id == conversation_id)
        
        # Delete conversation
        self.conversations_table.remove(Conversation.id == conversation_id)
        
        return True
    
    def search_conversations(self, query: str) -> List[Dict]:
        """Search conversations by title or content"""
        Conversation = Query()
        Message = Query()
        
        # Search by title
        title_matches = self.conversations_table.search(
            Conversation.title.matches(f'.*{query}.*', flags=re.IGNORECASE)
        )
        
        # Search by message content
        content_matches = self.messages_table.search(
            Message.content.matches(f'.*{query}.*', flags=re.IGNORECASE)
        )
        
        # Get unique conversation IDs from content matches
        content_conv_ids = list(set([msg['conversation_id'] for msg in content_matches]))
        content_conversations = []
        for conv_id in content_conv_ids:
            conv = self.conversations_table.search(Conversation.id == conv_id)
            if conv:
                content_conversations.extend(conv)
        
        # Combine and deduplicate
        all_conversations = title_matches + content_conversations
        seen_ids = set()
        unique_conversations = []
        
        for conv in all_conversations:
            if conv['id'] not in seen_ids:
                seen_ids.add(conv['id'])
                unique_conversations.append(conv)
        
        # Sort by last_interacted
        unique_conversations.sort(key=lambda x: x.get('last_interacted', ''), reverse=True)
        
        return unique_conversations
    
    def get_conversation_stats(self) -> Dict:
        """Get statistics about conversations"""
        all_conversations = self.conversations_table.all()
        all_messages = self.messages_table.all()
        
        return {
            'total_conversations': len(all_conversations),
            'total_messages': len(all_messages),
            'avg_messages_per_conversation': len(all_messages) / max(len(all_conversations), 1)
        }
    
    def cleanup_old_conversations(self, days_old: int = 30) -> int:
        """Remove conversations older than specified days"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        Conversation = Query()
        old_conversations = self.conversations_table.search(
            Conversation.last_interacted < datetime.fromtimestamp(cutoff_time).isoformat()
        )
        
        deleted_count = 0
        for conv in old_conversations:
            if self.delete_conversation(conv['id']):
                deleted_count += 1
        
        return deleted_count
    
    def close(self):
        """Close the database connection"""
        self.db.close()

# Global instance
conversation_manager = ConversationManager()
