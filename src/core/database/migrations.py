"""
Database Migration Management System
Handles schema version control and migrations for PostgreSQL

Author: Cavin Otieno
Version: 2.0.0-enterprise
"""

import asyncio
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import asyncpg
from pydantic import BaseModel, Field
import semver


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationStatus(BaseModel):
    """Migration status tracking"""
    migration_id: str
    version: str
    name: str
    status: str = Field(..., regex="^(pending|applied|failed|rolled_back)$")
    applied_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    checksum: Optional[str] = None


class MigrationMetadata(BaseModel):
    """Migration file metadata"""
    version: str
    name: str
    description: str
    author: str = "Cavin Otieno"
    dependencies: List[str] = []
    rollback_sql: Optional[str] = None
    checksum: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MigrationFile:
    """Represents a migration file"""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.metadata = self._parse_metadata()
        self.up_sql = self._extract_sql("UP")
        self.down_sql = self._extract_sql("DOWN")
        
    def _parse_metadata(self) -> MigrationMetadata:
        """Parse migration metadata from file header"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract metadata section
            metadata_match = re.search(r'-- Migration: (.+?)\n', content)
            if not metadata_match:
                raise ValueError(f"Missing migration metadata in {self.file_path}")
                
            metadata_str = metadata_match.group(1)
            
            # Parse key-value pairs
            metadata_dict = {}
            for line in metadata_str.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata_dict[key.strip()] = value.strip()
                    
            return MigrationMetadata(
                version=metadata_dict.get('version', ''),
                name=metadata_dict.get('name', ''),
                description=metadata_dict.get('description', ''),
                author=metadata_dict.get('author', 'Cavin Otieno'),
                dependencies=metadata_dict.get('dependencies', '').split(',') if metadata_dict.get('dependencies') else [],
                rollback_sql=metadata_dict.get('rollback_sql')
            )
            
        except Exception as e:
            logger.error(f"Error parsing metadata from {self.file_path}: {e}")
            raise
            
    def _extract_sql(self, section: str) -> str:
        """Extract SQL for UP or DOWN section"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find section
            pattern = rf'-- {section} SQL\n(.*?)(?=\n-- |\Z)'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                return match.group(1).strip()
            else:
                logger.warning(f"No {section} SQL found in {self.file_path}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting {section} SQL from {self.file_path}: {e}")
            return ""
            
    def calculate_checksum(self) -> str:
        """Calculate file checksum"""
        import hashlib
        with open(self.file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
            

class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, connection_string: str, migrations_dir: str = "database/migrations"):
        self.connection_string = connection_string
        self.migrations_dir = Path(migrations_dir)
        self.migrations_table = "schema_migrations"
        
    async def initialize(self) -> bool:
        """Initialize the migration system"""
        try:
            async with asyncpg.connect(self.connection_string) as conn:
                # Create migrations tracking table
                await conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                        migration_id VARCHAR(255) PRIMARY KEY,
                        version VARCHAR(100) NOT NULL UNIQUE,
                        name VARCHAR(500) NOT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'pending',
                        applied_at TIMESTAMP WITH TIME ZONE,
                        execution_time_ms INTEGER,
                        error_message TEXT,
                        checksum VARCHAR(64),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create index for better performance
                await conn.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_{self.migrations_table}_version 
                    ON {self.migrations_table}(version)
                ''')
                
                await conn.execute(f'''
                    CREATE INDEX IF NOT EXISTS idx_{self.migrations_table}_status 
                    ON {self.migrations_table}(status)
                ''')
                
            logger.info("Migration system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize migration system: {e}")
            return False
            
    async def get_applied_migrations(self) -> List[MigrationStatus]:
        """Get list of applied migrations"""
        try:
            async with asyncpg.connect(self.connection_string) as conn:
                rows = await conn.fetch(f'''
                    SELECT migration_id, version, name, status, applied_at, 
                           execution_time_ms, error_message, checksum
                    FROM {self.migrations_table}
                    ORDER BY version ASC
                ''')
                
                return [
                    MigrationStatus(
                        migration_id=row['migration_id'],
                        version=row['version'],
                        name=row['name'],
                        status=row['status'],
                        applied_at=row['applied_at'],
                        execution_time_ms=row['execution_time_ms'],
                        error_message=row['error_message'],
                        checksum=row['checksum']
                    )
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
            
    async def get_pending_migrations(self) -> List[MigrationFile]:
        """Get list of pending migrations"""
        try:
            # Load all migration files
            all_migrations = await self._load_migration_files()
            
            # Get applied migration versions
            applied_migrations = await self.get_applied_migrations()
            applied_versions = {m.version for m in applied_migrations if m.status == 'applied'}
            
            # Filter pending migrations
            pending_migrations = []
            for migration in all_migrations:
                if migration.metadata.version not in applied_versions:
                    pending_migrations.append(migration)
                    
            # Sort by version
            pending_migrations.sort(key=lambda x: x.metadata.version)
            
            return pending_migrations
            
        except Exception as e:
            logger.error(f"Failed to get pending migrations: {e}")
            return []
            
    async def apply_migration(self, migration_file: MigrationFile) -> bool:
        """Apply a single migration"""
        migration_id = str(uuid4())
        start_time = datetime.utcnow()
        
        try:
            # Validate migration dependencies
            if not await self._validate_dependencies(migration_file):
                logger.error(f"Migration {migration_file.metadata.version} has unmet dependencies")
                return False
                
            async with asyncpg.connect(self.connection_string) as conn:
                async with conn.transaction():
                    # Mark migration as pending
                    await conn.execute(f'''
                        INSERT INTO {self.migrations_table} 
                        (migration_id, version, name, status, checksum)
                        VALUES ($1, $2, $3, 'pending', $4)
                    ''', migration_id, migration_file.metadata.version, 
                       migration_file.metadata.name, migration_file.calculate_checksum())
                    
                    # Execute migration SQL
                    if migration_file.up_sql:
                        logger.info(f"Applying migration {migration_file.metadata.version}: {migration_file.metadata.name}")
                        await conn.execute(migration_file.up_sql)
                        
                        # Mark as applied
                        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                        
                        await conn.execute(f'''
                            UPDATE {self.migrations_table}
                            SET status = 'applied',
                                applied_at = $1,
                                execution_time_ms = $2,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE migration_id = $3
                        ''', datetime.utcnow(), execution_time, migration_id)
                        
                        logger.info(f"Migration {migration_file.metadata.version} applied successfully")
                        return True
                    else:
                        logger.warning(f"No UP SQL found for migration {migration_file.metadata.version}")
                        await conn.execute(f'''
                            UPDATE {self.migrations_table}
                            SET status = 'failed',
                                error_message = 'No UP SQL found',
                                updated_at = CURRENT_TIMESTAMP
                            WHERE migration_id = $1
                        ''', migration_id)
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_file.metadata.version}: {e}")
            
            # Mark migration as failed
            try:
                async with asyncpg.connect(self.connection_string) as conn:
                    await conn.execute(f'''
                        UPDATE {self.migrations_table}
                        SET status = 'failed',
                            error_message = $1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE migration_id = $2
                    ''', str(e), migration_id)
            except:
                pass
                
            return False
            
    async def rollback_migration(self, version: str) -> bool:
        """Rollback a migration"""
        try:
            # Find migration file
            migration_files = await self._load_migration_files()
            migration_file = next((m for m in migration_files if m.metadata.version == version), None)
            
            if not migration_file:
                logger.error(f"Migration file not found for version {version}")
                return False
                
            if not migration_file.down_sql:
                logger.error(f"No rollback SQL found for migration {version}")
                return False
                
            async with asyncpg.connect(self.connection_string) as conn:
                async with conn.transaction():
                    # Execute rollback SQL
                    logger.info(f"Rolling back migration {version}")
                    await conn.execute(migration_file.down_sql)
                    
                    # Mark as rolled back
                    await conn.execute(f'''
                        UPDATE {self.migrations_table}
                        SET status = 'rolled_back',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE version = $1
                    ''', version)
                    
                    logger.info(f"Migration {version} rolled back successfully")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to rollback migration {version}: {e}")
            return False
            
    async def apply_all_pending(self) -> Tuple[int, int]:
        """Apply all pending migrations"""
        pending_migrations = await self.get_pending_migrations()
        success_count = 0
        failure_count = 0
        
        logger.info(f"Found {len(pending_migrations)} pending migrations")
        
        for migration in pending_migrations:
            success = await self.apply_migration(migration)
            if success:
                success_count += 1
            else:
                failure_count += 1
                
            # Stop on first failure if configured
            if failure_count > 0:
                logger.warning("Stopping migration process due to failure")
                break
                
        logger.info(f"Migration process completed: {success_count} successful, {failure_count} failed")
        return success_count, failure_count
        
    async def get_migration_status(self) -> Dict[str, any]:
        """Get overall migration status"""
        applied = await self.get_applied_migrations()
        pending = await self.get_pending_migrations()
        failed = [m for m in applied if m.status == 'failed']
        
        # Get current database version
        current_version = None
        if applied:
            sorted_applied = sorted(applied, key=lambda x: x.version)
            current_version = sorted_applied[-1].version
            
        return {
            'current_version': current_version,
            'total_applied': len([m for m in applied if m.status == 'applied']),
            'total_pending': len(pending),
            'total_failed': len(failed),
            'migrations': applied
        }
        
    async def _load_migration_files(self) -> List[MigrationFile]:
        """Load all migration files from directory"""
        migration_files = []
        
        if not self.migrations_dir.exists():
            logger.warning(f"Migrations directory {self.migrations_dir} does not exist")
            return []
            
        # Find all SQL files
        sql_files = list(self.migrations_dir.glob("*.sql"))
        sql_files.sort()  # Sort by filename
        
        for sql_file in sql_files:
            try:
                migration = MigrationFile(sql_file)
                migration_files.append(migration)
            except Exception as e:
                logger.error(f"Failed to load migration file {sql_file}: {e}")
                
        return migration_files
        
    async def _validate_dependencies(self, migration: MigrationFile) -> bool:
        """Validate that all dependencies are met"""
        if not migration.metadata.dependencies:
            return True
            
        applied = await self.get_applied_migrations()
        applied_versions = {m.version for m in applied if m.status == 'applied'}
        
        for dependency in migration.metadata.dependencies:
            if dependency not in applied_versions:
                logger.error(f"Dependency {dependency} not met for migration {migration.metadata.version}")
                return False
                
        return True


class MigrationCreator:
    """Creates new migration files"""
    
    def __init__(self, migrations_dir: str = "database/migrations"):
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
    def create_migration(self, name: str, description: str, up_sql: str, down_sql: str = "") -> str:
        """Create a new migration file"""
        # Generate version
        version = self._generate_version()
        
        # Create filename
        filename = f"{version}_{name.lower().replace(' ', '_')}.sql"
        file_path = self.migrations_dir / filename
        
        # Create migration content
        content = self._generate_migration_content(
            version, name, description, up_sql, down_sql
        )
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Created migration file: {filename}")
        return filename
        
    def _generate_version(self) -> str:
        """Generate next version number"""
        existing_files = list(self.migrations_dir.glob("*.sql"))
        
        if not existing_files:
            return "001_initial_schema"
            
        # Extract versions and find next
        versions = []
        for file_path in existing_files:
            version_match = re.match(r'^(\d+)_', file_path.stem)
            if version_match:
                versions.append(int(version_match.group(1)))
                
        if not versions:
            return "001_add_feature"
            
        next_version = max(versions) + 1
        return f"{next_version:03d}_add_feature"
        
    def _generate_migration_content(self, version: str, name: str, description: str, 
                                  up_sql: str, down_sql: str) -> str:
        """Generate migration file content"""
        template = f"""-- Migration: version: {version}; name: {name}; description: {description}; author: Cavin Otieno; dependencies: 
-- Created: {datetime.utcnow().isoformat()}

-- UP SQL
{up_sql}

-- DOWN SQL
{down_sql}

-- End of migration
"""
        return template


# Migration commands
async def migrate_up(connection_string: str, migrations_dir: str = "database/migrations"):
    """Run migrations up"""
    manager = MigrationManager(connection_string, migrations_dir)
    
    # Initialize
    if not await manager.initialize():
        logger.error("Failed to initialize migration system")
        return
        
    # Apply pending migrations
    success_count, failure_count = await manager.apply_all_pending()
    
    # Print status
    status = await manager.get_migration_status()
    logger.info(f"Migration Status: {status}")
    
    if failure_count > 0:
        logger.error(f"Migration failed with {failure_count} errors")
    else:
        logger.info("All migrations applied successfully")


async def migrate_down(connection_string: str, version: str, migrations_dir: str = "database/migrations"):
    """Rollback to specific version"""
    manager = MigrationManager(connection_string, migrations_dir)
    
    # Get current status
    status = await manager.get_migration_status()
    
    if status['current_version'] == version:
        logger.info(f"Already at version {version}")
        return
        
    # Rollback migrations
    applied_migrations = await manager.get_applied_migrations()
    applied_versions = [m.version for m in applied_migrations if m.status == 'applied']
    
    # Find migrations to rollback
    migrations_to_rollback = []
    for applied_version in reversed(applied_versions):
        if applied_version == version:
            break
        migrations_to_rollback.append(applied_version)
        
    # Rollback each migration
    for migration_version in migrations_to_rollback:
        success = await manager.rollback_migration(migration_version)
        if not success:
            logger.error(f"Failed to rollback migration {migration_version}")
            break
            
    logger.info(f"Rolled back {len(migrations_to_rollback)} migrations")


async def migrate_status(connection_string: str, migrations_dir: str = "database/migrations"):
    """Show migration status"""
    manager = MigrationManager(connection_string, migrations_dir)
    status = await manager.get_migration_status()
    
    print(f"Current Version: {status['current_version'] or 'None'}")
    print(f"Total Applied: {status['total_applied']}")
    print(f"Total Pending: {status['total_pending']}")
    print(f"Total Failed: {status['total_failed']}")
    
    if status['migrations']:
        print("\nMigration History:")
        for migration in status['migrations']:
            print(f"  {migration.version}: {migration.name} ({migration.status})")
            if migration.error_message:
                print(f"    Error: {migration.error_message}")


def create_migration(name: str, description: str, up_sql: str, down_sql: str = "", 
                    migrations_dir: str = "database/migrations") -> str:
    """Create a new migration"""
    creator = MigrationCreator(migrations_dir)
    return creator.create_migration(name, description, up_sql, down_sql)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("command", choices=["up", "down", "status", "create"], 
                       help="Migration command")
    parser.add_argument("--db", default="postgresql://user:password@localhost/jaseci_learning", 
                       help="Database connection string")
    parser.add_argument("--dir", default="database/migrations", 
                       help="Migrations directory")
    parser.add_argument("--version", help="Target version for rollback")
    parser.add_argument("--name", help="Migration name (for create command)")
    parser.add_argument("--description", help="Migration description (for create command)")
    parser.add_argument("--up-sql", help="UP SQL (for create command)")
    parser.add_argument("--down-sql", default="", help="DOWN SQL (for create command)")
    
    args = parser.parse_args()
    
    if args.command == "up":
        asyncio.run(migrate_up(args.db, args.dir))
    elif args.command == "down":
        if not args.version:
            print("Error: --version required for down command")
            exit(1)
        asyncio.run(migrate_down(args.db, args.version, args.dir))
    elif args.command == "status":
        asyncio.run(migrate_status(args.db, args.dir))
    elif args.command == "create":
        if not all([args.name, args.description, args.up_sql]):
            print("Error: --name, --description, and --up-sql required for create command")
            exit(1)
        filename = create_migration(args.name, args.description, args.up_sql, args.down_sql, args.dir)
        print(f"Created migration: {filename}")