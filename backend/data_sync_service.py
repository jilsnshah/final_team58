"""
Data Sync Service - Continuous synchronization of Pathway JSONL files
Monitors database changes and triggers updates to propagate through Pathway
"""

import logging
import threading
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataSyncService:
    """Service to continuously sync data from Pathway to frontend"""
    
    def __init__(self, pathway_output_dir="./carbon-intelligence/server/output"):
        self.pathway_output_dir = pathway_output_dir
        self.running = False
        self.thread = None
        
        # Database config - use 'postgres' as default for Docker
        self.db_config = {
            'host': os.getenv('DB_HOST', 'postgres'),
            'port': os.getenv('DB_PORT', '5432'),
            'user': os.getenv('DB_USER', 'carbon'),
            'password': os.getenv('DB_PASSWORD', 'carbonpw'),
            'database': os.getenv('DB_NAME', 'carbon_intel')
        }
        
        # Track last update time to avoid redundant updates
        self.last_update = {
            'news': datetime.now(),
            'finance': datetime.now(),
            'verra': datetime.now()
        }
        
        logger.info("✅ Data Sync Service initialized")
    
    def start(self):
        """Start the background sync thread"""
        if self.running:
            logger.warning("⚠️ Data Sync Service already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
        logger.info("🚀 Data Sync Service started")
    
    def stop(self):
        """Stop the background sync thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("⛔ Data Sync Service stopped")
    
    def _get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return None
    
    def _trigger_news_update(self):
        """Trigger database update to propagate news to Kafka"""
        conn = self._get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            # Update all news records to trigger Debezium CDC
            cursor.execute("UPDATE news SET sentiment = sentiment LIMIT 200")
            count = cursor.rowcount
            conn.commit()
            cursor.close()
            
            if count > 0:
                logger.info(f"📰 Triggered news update: {count} records")
                self.last_update['news'] = datetime.now()
                return True
        except Exception as e:
            logger.error(f"❌ Failed to trigger news update: {e}")
        finally:
            conn.close()
        
        return False
    
    def _trigger_finance_update(self):
        """Trigger database update to propagate finance data"""
        conn = self._get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            # Update all finance records to trigger Debezium CDC
            cursor.execute("UPDATE finance SET price = price LIMIT 100")
            count = cursor.rowcount
            conn.commit()
            cursor.close()
            
            if count > 0:
                logger.info(f"💰 Triggered finance update: {count} records")
                self.last_update['finance'] = datetime.now()
                return True
        except Exception as e:
            logger.error(f"❌ Failed to trigger finance update: {e}")
        finally:
            conn.close()
        
        return False
    
    def _trigger_verra_update(self):
        """Trigger database update to propagate verra (carbon projects) data"""
        conn = self._get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            # Update verra records to trigger Debezium CDC
            cursor.execute("UPDATE verra SET project_id = project_id LIMIT 500")
            count = cursor.rowcount
            conn.commit()
            cursor.close()
            
            if count > 0:
                logger.info(f"🌱 Triggered verra update: {count} records")
                self.last_update['verra'] = datetime.now()
                return True
        except Exception as e:
            logger.error(f"❌ Failed to trigger verra update: {e}")
        finally:
            conn.close()
        
        return False
    
    def _sync_loop(self):
        """Main sync loop - runs in background thread"""
        logger.info("🔄 Data sync loop started")
        
        while self.running:
            try:
                # Update news every 90 seconds (faster updates)
                if datetime.now() - self.last_update['news'] > timedelta(seconds=90):
                    self._trigger_news_update()
                
                # Update finance every 120 seconds
                if datetime.now() - self.last_update['finance'] > timedelta(seconds=120):
                    self._trigger_finance_update()
                
                # Update verra/projects every 180 seconds (3 minutes)
                if datetime.now() - self.last_update['verra'] > timedelta(seconds=180):
                    self._trigger_verra_update()
                
                # Sleep before next check
                time.sleep(15)  # Check more frequently
                
            except Exception as e:
                logger.error(f"❌ Error in sync loop: {e}")
                time.sleep(30)
        
        logger.info("🔄 Data sync loop ended")

# Global instance
_sync_service = None

def get_data_sync_service():
    """Get or create the global data sync service"""
    global _sync_service
    if _sync_service is None:
        _sync_service = DataSyncService()
    return _sync_service
