#!/usr/bin/env python3
"""
Database Viewer Script
This script allows you to view all data in your SQLite database
"""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models

def view_database():
    """View all data in the database"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*80)
        print("DATABASE CONTENTS")
        print("="*80)
        
        # View Users
        print("\n📊 USERS TABLE")
        print("-" * 80)
        users = db.query(models.User).all()
        if users:
            for user in users:
                print(f"ID: {user.id}")
                print(f"  Voice Preference: {user.voice_preference}")
                print(f"  Message Count: {user.message_count}")
                print(f"  First Seen: {user.first_seen}")
                print(f"  Last Seen: {user.last_seen}")
                print()
        else:
            print("No users found.")
        
        # View Messages
        print("\n💬 MESSAGES TABLE")
        print("-" * 80)
        messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(10).all()
        if messages:
            print(f"Showing last 10 messages (Total: {db.query(models.Message).count()})")
            print()
            for msg in messages:
                print(f"ID: {msg.id} | User: {msg.user_id} | Agent: {msg.agent_id}")
                print(f"  Timestamp: {msg.timestamp}")
                print(f"  User Message: {msg.user_message[:100]}...")
                print(f"  Agent Reply: {msg.agent_reply[:100]}...")
                print()
        else:
            print("No messages found.")
        
        # View Transactions
        print("\n💳 TRANSACTIONS TABLE")
        print("-" * 80)
        transactions = db.query(models.Transaction).all()
        if transactions:
            for txn in transactions:
                print(f"ID: {txn.id}")
                print(f"  Session ID: {txn.session_id}")
                print(f"  Amount: ${txn.amount} {txn.currency.upper()}")
                print(f"  User ID: {txn.user_id}")
                print(f"  Status: {txn.status}")
                print(f"  Timestamp: {txn.timestamp}")
                print()
        else:
            print("No transactions found.")
        
        # View Analytics
        print("\n📈 ANALYTICS TABLE")
        print("-" * 80)
        analytics = db.query(models.Analytics).first()
        if analytics:
            print(f"Page Views: {analytics.page_views}")
        else:
            print("No analytics data found.")
        
        # Summary Statistics
        print("\n📊 SUMMARY STATISTICS")
        print("-" * 80)
        total_users = db.query(models.User).count()
        total_messages = db.query(models.Message).count()
        total_transactions = db.query(models.Transaction).count()
        
        print(f"Total Users: {total_users}")
        print(f"Total Messages: {total_messages}")
        print(f"Total Transactions: {total_transactions}")
        
        # Agent usage statistics
        from sqlalchemy import func
        agent_stats = db.query(
            models.Message.agent_id, 
            func.count(models.Message.id).label('count')
        ).group_by(models.Message.agent_id).all()
        
        if agent_stats:
            print("\nMessages by Agent:")
            for agent, count in agent_stats:
                print(f"  {agent}: {count} messages")
        
        print("\n" + "="*80)
        
    finally:
        db.close()

if __name__ == "__main__":
    view_database()
