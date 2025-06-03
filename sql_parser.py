import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML
import re
from collections import defaultdict, Counter

class SQLParser:
    """Parse SQL files and extract table and field information"""
    
    def __init__(self):
        self.tables = set()
        self.fields = set()
        self.table_occurrences = defaultdict(int)
        self.field_occurrences = defaultdict(int)
        self.statement_types = defaultdict(int)
        self.statements = []
    
    def parse_sql(self, sql_content):
        """Parse SQL content and extract relevant information"""
        try:
            # Parse the SQL content
            parsed_statements = sqlparse.parse(sql_content)
            
            for statement in parsed_statements:
                if statement.tokens:
                    # Clean and store the statement
                    clean_stmt = str(statement).strip()
                    if clean_stmt:
                        self.statements.append(clean_stmt)
                        
                        # Get statement type
                        stmt_type = self._get_statement_type(statement)
                        if stmt_type:
                            self.statement_types[stmt_type] += 1
                        
                        # Extract tables and fields
                        self._extract_from_statement(statement)
            
            return {
                'statements': self.statements,
                'tables': self.tables,
                'fields': self.fields,
                'table_occurrences': dict(self.table_occurrences),
                'field_occurrences': dict(self.field_occurrences),
                'statement_types': dict(self.statement_types)
            }
            
        except Exception as e:
            raise Exception(f"Error parsing SQL content: {str(e)}")
    
    def _get_statement_type(self, statement):
        """Determine the type of SQL statement"""
        first_token = statement.token_first(skip_ws=True, skip_cm=True)
        if first_token and first_token.ttype is Keyword:
            return first_token.value.upper()
        return "UNKNOWN"
    
    def _extract_from_statement(self, statement):
        """Extract tables and fields from a SQL statement"""
        # Convert statement to string for regex parsing
        stmt_str = str(statement).upper()
        
        # Extract table names from various SQL clauses
        self._extract_tables_from_clauses(stmt_str)
        
        # Extract field names
        self._extract_fields_from_statement(statement)
    
    def _extract_tables_from_clauses(self, stmt_str):
        """Extract table names from FROM, JOIN, UPDATE, INSERT INTO clauses"""
        # FROM clause
        from_pattern = r'\bFROM\s+(\w+(?:\.\w+)?)'
        from_matches = re.findall(from_pattern, stmt_str, re.IGNORECASE)
        
        # JOIN clauses
        join_pattern = r'\bJOIN\s+(\w+(?:\.\w+)?)'
        join_matches = re.findall(join_pattern, stmt_str, re.IGNORECASE)
        
        # UPDATE clause
        update_pattern = r'\bUPDATE\s+(\w+(?:\.\w+)?)'
        update_matches = re.findall(update_pattern, stmt_str, re.IGNORECASE)
        
        # INSERT INTO clause
        insert_pattern = r'\bINSERT\s+INTO\s+(\w+(?:\.\w+)?)'
        insert_matches = re.findall(insert_pattern, stmt_str, re.IGNORECASE)
        
        # DELETE FROM clause
        delete_pattern = r'\bDELETE\s+FROM\s+(\w+(?:\.\w+)?)'
        delete_matches = re.findall(delete_pattern, stmt_str, re.IGNORECASE)
        
        # Combine all matches
        all_tables = from_matches + join_matches + update_matches + insert_matches + delete_matches
        
        for table in all_tables:
            # Handle schema.table format
            table_name = table.split('.')[-1].strip('`"[]')
            if table_name and not self._is_sql_keyword(table_name):
                self.tables.add(table_name.lower())
                self.table_occurrences[table_name.lower()] += 1
    
    def _extract_fields_from_statement(self, statement):
        """Extract field names from SELECT, WHERE, ORDER BY clauses"""
        stmt_str = str(statement)
        
        # Extract from SELECT list
        self._extract_fields_from_select(stmt_str)
        
        # Extract from WHERE conditions
        self._extract_fields_from_where(stmt_str)
        
        # Extract from ORDER BY
        self._extract_fields_from_order_by(stmt_str)
        
        # Extract from GROUP BY
        self._extract_fields_from_group_by(stmt_str)
        
        # Extract from INSERT columns
        self._extract_fields_from_insert(stmt_str)
        
        # Extract from UPDATE SET
        self._extract_fields_from_update(stmt_str)
    
    def _extract_fields_from_select(self, stmt_str):
        """Extract field names from SELECT clause"""
        # Simple regex to find SELECT fields
        select_pattern = r'\bSELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, stmt_str, re.IGNORECASE | re.DOTALL)
        
        if select_match:
            select_list = select_match.group(1)
            # Split by comma and clean up
            fields = [f.strip() for f in select_list.split(',')]
            
            for field in fields:
                # Remove aliases and functions
                field = re.sub(r'\s+AS\s+\w+', '', field, flags=re.IGNORECASE)
                field = self._clean_field_name(field)
                
                if field and field != '*' and not self._is_sql_keyword(field):
                    # Handle table.field format
                    if '.' in field:
                        field = field.split('.')[-1]
                    
                    field = field.strip('`"[]').lower()
                    if field:
                        self.fields.add(field)
                        self.field_occurrences[field] += 1
    
    def _extract_fields_from_where(self, stmt_str):
        """Extract field names from WHERE clause"""
        where_pattern = r'\bWHERE\s+(.*?)(?:\s+(?:GROUP|ORDER|HAVING|LIMIT|$))'
        where_match = re.search(where_pattern, stmt_str, re.IGNORECASE | re.DOTALL)
        
        if where_match:
            where_clause = where_match.group(1)
            # Extract field names (simple approach)
            field_pattern = r'\b(\w+(?:\.\w+)?)\s*(?:=|<|>|!=|<>|LIKE|IN|BETWEEN)'
            field_matches = re.findall(field_pattern, where_clause, re.IGNORECASE)
            
            for field in field_matches:
                if '.' in field:
                    field = field.split('.')[-1]
                
                field = field.strip('`"[]').lower()
                if field and not self._is_sql_keyword(field):
                    self.fields.add(field)
                    self.field_occurrences[field] += 1
    
    def _extract_fields_from_order_by(self, stmt_str):
        """Extract field names from ORDER BY clause"""
        order_pattern = r'\bORDER\s+BY\s+(.*?)(?:\s+(?:LIMIT|$))'
        order_match = re.search(order_pattern, stmt_str, re.IGNORECASE | re.DOTALL)
        
        if order_match:
            order_clause = order_match.group(1)
            fields = [f.strip() for f in order_clause.split(',')]
            
            for field in fields:
                # Remove ASC/DESC
                field = re.sub(r'\s+(ASC|DESC)$', '', field, flags=re.IGNORECASE)
                field = self._clean_field_name(field)
                
                if '.' in field:
                    field = field.split('.')[-1]
                
                field = field.strip('`"[]').lower()
                if field and not self._is_sql_keyword(field):
                    self.fields.add(field)
                    self.field_occurrences[field] += 1
    
    def _extract_fields_from_group_by(self, stmt_str):
        """Extract field names from GROUP BY clause"""
        group_pattern = r'\bGROUP\s+BY\s+(.*?)(?:\s+(?:HAVING|ORDER|LIMIT|$))'
        group_match = re.search(group_pattern, stmt_str, re.IGNORECASE | re.DOTALL)
        
        if group_match:
            group_clause = group_match.group(1)
            fields = [f.strip() for f in group_clause.split(',')]
            
            for field in fields:
                field = self._clean_field_name(field)
                
                if '.' in field:
                    field = field.split('.')[-1]
                
                field = field.strip('`"[]').lower()
                if field and not self._is_sql_keyword(field):
                    self.fields.add(field)
                    self.field_occurrences[field] += 1
    
    def _extract_fields_from_insert(self, stmt_str):
        """Extract field names from INSERT statement"""
        insert_pattern = r'\bINSERT\s+INTO\s+\w+\s*\((.*?)\)'
        insert_match = re.search(insert_pattern, stmt_str, re.IGNORECASE | re.DOTALL)
        
        if insert_match:
            fields_list = insert_match.group(1)
            fields = [f.strip() for f in fields_list.split(',')]
            
            for field in fields:
                field = field.strip('`"[]').lower()
                if field and not self._is_sql_keyword(field):
                    self.fields.add(field)
                    self.field_occurrences[field] += 1
    
    def _extract_fields_from_update(self, stmt_str):
        """Extract field names from UPDATE SET clause"""
        set_pattern = r'\bSET\s+(.*?)\s+WHERE'
        set_match = re.search(set_pattern, stmt_str, re.IGNORECASE | re.DOTALL)
        
        if set_match:
            set_clause = set_match.group(1)
            # Extract field names before = sign
            field_pattern = r'(\w+)\s*='
            field_matches = re.findall(field_pattern, set_clause, re.IGNORECASE)
            
            for field in field_matches:
                field = field.strip('`"[]').lower()
                if field and not self._is_sql_keyword(field):
                    self.fields.add(field)
                    self.field_occurrences[field] += 1
    
    def _clean_field_name(self, field):
        """Clean field name by removing functions and special characters"""
        # Remove common SQL functions
        field = re.sub(r'\b(?:COUNT|SUM|AVG|MAX|MIN|DISTINCT)\s*\(\s*(.*?)\s*\)', r'\1', field, flags=re.IGNORECASE)
        
        # Remove parentheses
        field = re.sub(r'[()]', '', field)
        
        # Remove extra whitespace
        field = field.strip()
        
        return field
    
    def _is_sql_keyword(self, word):
        """Check if a word is a SQL keyword"""
        sql_keywords = {
            'select', 'from', 'where', 'join', 'inner', 'left', 'right', 'outer',
            'union', 'order', 'by', 'group', 'having', 'limit', 'offset',
            'insert', 'into', 'values', 'update', 'set', 'delete', 'create',
            'table', 'index', 'view', 'drop', 'alter', 'add', 'column',
            'primary', 'key', 'foreign', 'references', 'constraint', 'unique',
            'not', 'null', 'default', 'auto_increment', 'varchar', 'int',
            'integer', 'decimal', 'float', 'double', 'text', 'date', 'datetime',
            'timestamp', 'boolean', 'true', 'false', 'and', 'or', 'in', 'like',
            'between', 'exists', 'case', 'when', 'then', 'else', 'end', 'as',
            'distinct', 'count', 'sum', 'avg', 'max', 'min', 'asc', 'desc'
        }
        return word.lower() in sql_keywords
