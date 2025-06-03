import pandas as pd
from collections import defaultdict

class SchemaAnalyzer:
    """Analyze and compare schema against SQL content"""
    
    def __init__(self):
        pass
    
    def analyze(self, parsed_sql_data, schema_df):
        """
        Analyze the parsed SQL data against the reference schema
        
        Args:
            parsed_sql_data: Dictionary containing parsed SQL information
            schema_df: DataFrame containing reference schema (table_name, field_name columns)
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Normalize schema data
            schema_df = self._normalize_schema_data(schema_df)
            
            # Generate comparison report
            comparison_report = self._generate_comparison_report(parsed_sql_data, schema_df)
            
            # Get usage statistics
            table_usage = parsed_sql_data.get('table_occurrences', {})
            field_usage = parsed_sql_data.get('field_occurrences', {})
            
            return {
                'comparison_report': comparison_report,
                'table_usage': table_usage,
                'field_usage': field_usage,
                'sql_tables': parsed_sql_data.get('tables', set()),
                'sql_fields': parsed_sql_data.get('fields', set()),
                'schema_tables': set(schema_df['table_name'].str.lower().unique()),
                'schema_fields': set(schema_df['field_name'].str.lower().unique())
            }
            
        except Exception as e:
            raise Exception(f"Error in schema analysis: {str(e)}")
    
    def _normalize_schema_data(self, schema_df):
        """Normalize schema data for comparison"""
        # Create a copy to avoid modifying original
        normalized_df = schema_df.copy()
        
        # Convert to lowercase for case-insensitive comparison
        normalized_df['table_name'] = normalized_df['table_name'].astype(str).str.lower().str.strip()
        normalized_df['field_name'] = normalized_df['field_name'].astype(str).str.lower().str.strip()
        
        # Remove any empty or null values
        normalized_df = normalized_df.dropna()
        normalized_df = normalized_df[
            (normalized_df['table_name'] != '') & 
            (normalized_df['field_name'] != '')
        ]
        
        return normalized_df
    
    def _generate_comparison_report(self, parsed_sql_data, schema_df):
        """Generate detailed comparison report"""
        sql_tables = set(parsed_sql_data.get('tables', []))
        sql_fields = set(parsed_sql_data.get('fields', []))
        table_occurrences = parsed_sql_data.get('table_occurrences', {})
        field_occurrences = parsed_sql_data.get('field_occurrences', {})
        
        comparison_data = []
        
        # Check each schema item against SQL content
        for _, row in schema_df.iterrows():
            table_name = row['table_name']
            field_name = row['field_name']
            
            # Check if table exists in SQL
            table_found = table_name in sql_tables
            table_count = table_occurrences.get(table_name, 0)
            
            # Check if field exists in SQL
            field_found = field_name in sql_fields
            field_count = field_occurrences.get(field_name, 0)
            
            # Determine overall found status
            # Consider it found if either table or field is found
            overall_found = table_found or field_found
            total_occurrences = max(table_count, field_count)
            
            comparison_data.append({
                'table_name': table_name,
                'field_name': field_name,
                'table_found': table_found,
                'field_found': field_found,
                'found': overall_found,
                'table_occurrences': table_count,
                'field_occurrences': field_count,
                'occurrences': total_occurrences,
                'status': 'Found' if overall_found else 'Not Found'
            })
        
        return pd.DataFrame(comparison_data)
    
    def get_schema_coverage_stats(self, analysis_results):
        """Calculate coverage statistics"""
        comparison_report = analysis_results['comparison_report']
        
        if comparison_report.empty:
            return {
                'total_schema_items': 0,
                'found_items': 0,
                'not_found_items': 0,
                'coverage_percentage': 0,
                'table_coverage': 0,
                'field_coverage': 0
            }
        
        total_items = len(comparison_report)
        found_items = len(comparison_report[comparison_report['found'] == True])
        not_found_items = total_items - found_items
        coverage_percentage = (found_items / total_items * 100) if total_items > 0 else 0
        
        # Table-specific coverage
        table_items = len(comparison_report['table_name'].unique())
        found_tables = len(comparison_report[comparison_report['table_found'] == True]['table_name'].unique())
        table_coverage = (found_tables / table_items * 100) if table_items > 0 else 0
        
        # Field-specific coverage
        field_items = len(comparison_report['field_name'].unique())
        found_fields = len(comparison_report[comparison_report['field_found'] == True]['field_name'].unique())
        field_coverage = (found_fields / field_items * 100) if field_items > 0 else 0
        
        return {
            'total_schema_items': total_items,
            'found_items': found_items,
            'not_found_items': not_found_items,
            'coverage_percentage': round(coverage_percentage, 2),
            'table_coverage': round(table_coverage, 2),
            'field_coverage': round(field_coverage, 2),
            'unique_tables': table_items,
            'unique_fields': field_items,
            'found_unique_tables': found_tables,
            'found_unique_fields': found_fields
        }
    
    def get_unused_schema_items(self, analysis_results):
        """Get schema items that are not used in SQL"""
        comparison_report = analysis_results['comparison_report']
        
        if comparison_report.empty:
            return pd.DataFrame()
        
        unused_items = comparison_report[comparison_report['found'] == False]
        return unused_items[['table_name', 'field_name']].sort_values(['table_name', 'field_name'])
    
    def get_sql_only_items(self, analysis_results):
        """Get tables and fields found in SQL but not in schema"""
        sql_tables = analysis_results['sql_tables']
        sql_fields = analysis_results['sql_fields']
        schema_tables = analysis_results['schema_tables']
        schema_fields = analysis_results['schema_fields']
        
        # Tables in SQL but not in schema
        sql_only_tables = sql_tables - schema_tables
        
        # Fields in SQL but not in schema
        sql_only_fields = sql_fields - schema_fields
        
        return {
            'tables': sorted(list(sql_only_tables)),
            'fields': sorted(list(sql_only_fields))
        }
    
    def generate_summary_report(self, analysis_results):
        """Generate a comprehensive summary report"""
        coverage_stats = self.get_schema_coverage_stats(analysis_results)
        unused_items = self.get_unused_schema_items(analysis_results)
        sql_only_items = self.get_sql_only_items(analysis_results)
        
        return {
            'coverage_statistics': coverage_stats,
            'unused_schema_items': unused_items,
            'sql_only_items': sql_only_items,
            'table_usage': analysis_results['table_usage'],
            'field_usage': analysis_results['field_usage']
        }
