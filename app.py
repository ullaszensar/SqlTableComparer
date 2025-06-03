import streamlit as st
import pandas as pd
import io
from datetime import datetime
from sql_parser import SQLParser
from schema_analyzer import SchemaAnalyzer

def main():
    st.set_page_config(
        page_title="SQL Schema Comparison Tool",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 SQL Schema Comparison Tool")
    st.markdown("Compare multiple SQL files against reference database schemas with occurrence tracking and comprehensive reporting.")
    
    # Sidebar for file uploads
    st.sidebar.header("📁 File Uploads")
    
    # SQL files upload (multiple)
    sql_files = st.sidebar.file_uploader(
        "Upload SQL Files",
        type=['sql', 'txt'],
        help="Upload multiple SQL files for analysis",
        accept_multiple_files=True
    )
    
    # Reference schema file upload
    schema_file = st.sidebar.file_uploader(
        "Upload Reference Schema",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel file containing table and field details"
    )
    
    if sql_files and schema_file:
        try:
            # Process multiple SQL files
            all_parsed_data = {}
            combined_tables = {}
            combined_fields = {}
            
            for sql_file in sql_files:
                # Process each SQL file
                sql_content = sql_file.read().decode('utf-8')
                parser = SQLParser()
                parsed_data = parser.parse_sql(sql_content)
                all_parsed_data[sql_file.name] = parsed_data
                
                # Combine table and field occurrences
                for table, count in parsed_data.get('table_occurrences', {}).items():
                    if table not in combined_tables:
                        combined_tables[table] = {}
                    combined_tables[table][sql_file.name] = count
                
                for field, count in parsed_data.get('field_occurrences', {}).items():
                    if field not in combined_fields:
                        combined_fields[field] = {}
                    combined_fields[field][sql_file.name] = count
            
            # Process schema file
            if schema_file.name.endswith('.csv'):
                schema_df = pd.read_csv(schema_file)
            else:
                schema_df = pd.read_excel(schema_file)
            
            # Validate schema format
            if not validate_schema_format(schema_df):
                st.error("❌ Invalid schema file format. Please ensure your file has 'table_name' and 'field_name' columns.")
                return
            
            # Display results in tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📁 Files & Tables Analysis", 
                "📋 Files & Fields Analysis", 
                "📋 Complete SQL Inventory",
                "📊 Schema Comparison", 
                "📈 Individual File Analysis"
            ])
            
            with tab1:
                display_files_tables_analysis(all_parsed_data, combined_tables)
            
            with tab2:
                display_files_fields_analysis(all_parsed_data, combined_fields)
            
            with tab3:
                display_complete_sql_inventory(all_parsed_data, combined_tables, combined_fields)
            
            with tab4:
                # Create combined data for schema comparison
                combined_parsed_data = combine_all_parsed_data(all_parsed_data)
                analyzer = SchemaAnalyzer()
                analysis_results = analyzer.analyze(combined_parsed_data, schema_df)
                display_comparison_report(analysis_results)
            
            with tab5:
                display_individual_file_analysis(all_parsed_data, schema_df)
            
            # Add HTML report generation buttons
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("📄 Generate Complete HTML Report", use_container_width=True):
                    html_report = generate_html_report(all_parsed_data, combined_tables, combined_fields, schema_df)
                    st.download_button(
                        label="📥 Download Complete Report",
                        data=html_report,
                        file_name="sql_analysis_report.html",
                        mime="text/html",
                        use_container_width=True
                    )
            
            with col3:
                if st.button("📊 Generate Schema Comparison Report", use_container_width=True):
                    combined_parsed_data = combine_all_parsed_data(all_parsed_data)
                    analyzer = SchemaAnalyzer()
                    analysis_results = analyzer.analyze(combined_parsed_data, schema_df)
                    schema_html_report = generate_schema_comparison_html_report(analysis_results, schema_df, all_parsed_data)
                    st.download_button(
                        label="📥 Download Schema Comparison",
                        data=schema_html_report,
                        file_name="schema_comparison_report.html",
                        mime="text/html",
                        use_container_width=True
                    )
                
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
            st.info("Please check your file formats and try again.")
    
    elif sql_files and not schema_file:
        try:
            # Process SQL files without schema comparison
            all_parsed_data = {}
            combined_tables = {}
            combined_fields = {}
            
            for sql_file in sql_files:
                sql_content = sql_file.read().decode('utf-8')
                parser = SQLParser()
                parsed_data = parser.parse_sql(sql_content)
                all_parsed_data[sql_file.name] = parsed_data
                
                for table, count in parsed_data.get('table_occurrences', {}).items():
                    if table not in combined_tables:
                        combined_tables[table] = {}
                    combined_tables[table][sql_file.name] = count
                
                for field, count in parsed_data.get('field_occurrences', {}).items():
                    if field not in combined_fields:
                        combined_fields[field] = {}
                    combined_fields[field][sql_file.name] = count
            
            # Display SQL-only analysis tabs
            tab1, tab2, tab3, tab4 = st.tabs([
                "📁 Files & Tables Analysis", 
                "📋 Files & Fields Analysis", 
                "📋 Complete SQL Inventory",
                "📈 Individual File Analysis"
            ])
            
            with tab1:
                display_files_tables_analysis(all_parsed_data, combined_tables)
            
            with tab2:
                display_files_fields_analysis(all_parsed_data, combined_fields)
            
            with tab3:
                display_complete_sql_inventory(all_parsed_data, combined_tables, combined_fields)
            
            with tab4:
                display_individual_file_analysis_no_schema(all_parsed_data)
            
            # Add HTML report generation button for SQL-only analysis
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("📄 Generate Complete SQL Analysis HTML Report", use_container_width=True):
                    html_report = generate_sql_inventory_html_report(all_parsed_data, combined_tables, combined_fields)
                    st.download_button(
                        label="📥 Download SQL Analysis HTML Report",
                        data=html_report,
                        file_name="sql_analysis_report.html",
                        mime="text/html",
                        use_container_width=True
                    )
                    
        except Exception as e:
            st.error(f"❌ Error processing SQL files: {str(e)}")
            st.info("Please check your file formats and try again.")
    
    elif schema_file and not sql_files:
        st.warning("⚠️ Please upload SQL files for analysis.")
    else:
        st.info("👆 Please upload SQL files to begin analysis. Upload a reference schema file for additional comparison features.")
        
        # Display help information
        with st.expander("ℹ️ How to use this tool"):
            st.markdown("""
            ### SQL File Requirements:
            - Supported formats: `.sql`, `.txt`
            - Should contain valid SQL statements
            - Supports multiple SQL dialects (MySQL, PostgreSQL, SQL Server, etc.)
            - You can select multiple files for batch analysis
            
            ### Reference Schema File Requirements:
            - Supported formats: `.csv`, `.xlsx`, `.xls`
            - Must contain at least two columns:
              - `table_name`: Name of database tables
              - `field_name`: Name of fields/columns in each table
            
            ### Example Schema File Format:
            ```
            table_name,field_name
            users,user_id
            users,username
            users,email
            orders,order_id
            orders,user_id
            orders,total_amount
            ```
            """)

def combine_all_parsed_data(all_parsed_data):
    """Combine parsed data from all SQL files"""
    combined_tables = set()
    combined_fields = set()
    combined_table_occurrences = {}
    combined_field_occurrences = {}
    combined_statements = []
    combined_statement_types = {}
    
    for file_name, parsed_data in all_parsed_data.items():
        combined_tables.update(parsed_data.get('tables', set()))
        combined_fields.update(parsed_data.get('fields', set()))
        combined_statements.extend(parsed_data.get('statements', []))
        
        # Combine occurrences
        for table, count in parsed_data.get('table_occurrences', {}).items():
            combined_table_occurrences[table] = combined_table_occurrences.get(table, 0) + count
        
        for field, count in parsed_data.get('field_occurrences', {}).items():
            combined_field_occurrences[field] = combined_field_occurrences.get(field, 0) + count
        
        for stmt_type, count in parsed_data.get('statement_types', {}).items():
            combined_statement_types[stmt_type] = combined_statement_types.get(stmt_type, 0) + count
    
    return {
        'tables': combined_tables,
        'fields': combined_fields,
        'table_occurrences': combined_table_occurrences,
        'field_occurrences': combined_field_occurrences,
        'statements': combined_statements,
        'statement_types': combined_statement_types
    }

def display_files_tables_analysis(all_parsed_data, combined_tables):
    """Display files and tables analysis with occurrences"""
    st.header("📁 Files & Tables Analysis")
    
    # Create a comprehensive table showing files and their tables
    analysis_data = []
    
    for file_name, parsed_data in all_parsed_data.items():
        tables = parsed_data.get('table_occurrences', {})
        if tables:
            for table, count in tables.items():
                analysis_data.append({
                    'File Name': file_name,
                    'Table Name': table,
                    'Occurrences': count
                })
        else:
            analysis_data.append({
                'File Name': file_name,
                'Table Name': 'No tables found',
                'Occurrences': 0
            })
    
    if analysis_data:
        analysis_df = pd.DataFrame(analysis_data)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Files", len(all_parsed_data))
        col2.metric("Unique Tables", len(combined_tables))
        col3.metric("Total Table References", sum(row['Occurrences'] for row in analysis_data))
        col4.metric("Avg Tables per File", f"{len(combined_tables) / len(all_parsed_data):.1f}")
        
        # Filter options
        st.subheader("📊 Detailed Analysis")
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_file = st.selectbox("Filter by File", ["All Files"] + sorted(list(all_parsed_data.keys())))
        with filter_col2:
            selected_table = st.selectbox("Filter by Table", ["All Tables"] + sorted(list(combined_tables)))
        
        # Apply filters
        filtered_df = analysis_df.copy()
        if selected_file != "All Files":
            filtered_df = filtered_df[filtered_df['File Name'] == selected_file]
        if selected_table != "All Tables":
            filtered_df = filtered_df[filtered_df['Table Name'] == selected_table]
        
        # Display table
        st.dataframe(filtered_df, use_container_width=True)
        
        # Table usage summary
        st.subheader("📋 Table Usage Summary")
        table_summary = []
        for table in sorted(combined_tables):
            files_using_table = []
            total_occurrences = 0
            for file_name, parsed_data in all_parsed_data.items():
                if table in parsed_data.get('table_occurrences', {}):
                    count = parsed_data['table_occurrences'][table]
                    files_using_table.append(f"{file_name} ({count})")
                    total_occurrences += count
            
            table_summary.append({
                'Table Name': table,
                'Files Using': len(files_using_table),
                'Total Occurrences': total_occurrences,
                'Files Details': ', '.join(files_using_table)
            })
        
        if table_summary:
            summary_df = pd.DataFrame(table_summary)
            st.dataframe(summary_df, use_container_width=True)
        
        # Download button
        csv_buffer = io.StringIO()
        analysis_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Files & Tables Analysis (CSV)",
            data=csv_buffer.getvalue(),
            file_name="files_tables_analysis.csv",
            mime="text/csv"
        )

def display_files_fields_analysis(all_parsed_data, combined_fields):
    """Display files and fields analysis with occurrences"""
    st.header("📋 Files & Fields Analysis")
    
    # Create a comprehensive table showing files and their fields
    analysis_data = []
    
    for file_name, parsed_data in all_parsed_data.items():
        fields = parsed_data.get('field_occurrences', {})
        if fields:
            for field, count in fields.items():
                analysis_data.append({
                    'File Name': file_name,
                    'Field Name': field,
                    'Occurrences': count
                })
        else:
            analysis_data.append({
                'File Name': file_name,
                'Field Name': 'No fields found',
                'Occurrences': 0
            })
    
    if analysis_data:
        analysis_df = pd.DataFrame(analysis_data)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Files", len(all_parsed_data))
        col2.metric("Unique Fields", len(combined_fields))
        col3.metric("Total Field References", sum(row['Occurrences'] for row in analysis_data))
        col4.metric("Avg Fields per File", f"{len(combined_fields) / len(all_parsed_data):.1f}")
        
        # Filter options
        st.subheader("📊 Detailed Analysis")
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            selected_file = st.selectbox("Filter by File", ["All Files"] + sorted(list(all_parsed_data.keys())), key="fields_file_filter")
        with filter_col2:
            selected_field = st.selectbox("Filter by Field", ["All Fields"] + sorted(list(combined_fields)), key="fields_field_filter")
        
        # Apply filters
        filtered_df = analysis_df.copy()
        if selected_file != "All Files":
            filtered_df = filtered_df[filtered_df['File Name'] == selected_file]
        if selected_field != "All Fields":
            filtered_df = filtered_df[filtered_df['Field Name'] == selected_field]
        
        # Display table
        st.dataframe(filtered_df, use_container_width=True)
        
        # Field usage summary
        st.subheader("🏷️ Field Usage Summary")
        field_summary = []
        for field in sorted(combined_fields):
            files_using_field = []
            total_occurrences = 0
            for file_name, parsed_data in all_parsed_data.items():
                if field in parsed_data.get('field_occurrences', {}):
                    count = parsed_data['field_occurrences'][field]
                    files_using_field.append(f"{file_name} ({count})")
                    total_occurrences += count
            
            field_summary.append({
                'Field Name': field,
                'Files Using': len(files_using_field),
                'Total Occurrences': total_occurrences,
                'Files Details': ', '.join(files_using_field)
            })
        
        if field_summary:
            summary_df = pd.DataFrame(field_summary)
            st.dataframe(summary_df, use_container_width=True)
        
        # Download button
        csv_buffer = io.StringIO()
        analysis_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Files & Fields Analysis (CSV)",
            data=csv_buffer.getvalue(),
            file_name="files_fields_analysis.csv",
            mime="text/csv"
        )

def display_complete_sql_inventory(all_parsed_data, combined_tables, combined_fields):
    """Display complete inventory of all tables and fields found in SQL files"""
    st.header("📋 Complete SQL Inventory")
    st.markdown("This section lists all tables and fields discovered in your SQL files, regardless of schema comparison.")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    total_files = len(all_parsed_data)
    total_unique_tables = len(combined_tables)
    total_unique_fields = len(combined_fields)
    total_statements = sum(len(data.get('statements', [])) for data in all_parsed_data.values())
    
    col1.metric("Total SQL Files", total_files)
    col2.metric("Unique Tables", total_unique_tables)
    col3.metric("Unique Fields", total_unique_fields)
    col4.metric("Total SQL Statements", total_statements)
    
    # Tables inventory
    st.subheader("📋 All Tables Found")
    if combined_tables:
        # Create table inventory with source files
        table_inventory = []
        for table in sorted(combined_tables):
            source_files = []
            total_occurrences = 0
            for file_name, parsed_data in all_parsed_data.items():
                if table in parsed_data.get('table_occurrences', {}):
                    count = parsed_data['table_occurrences'][table]
                    source_files.append(f"{file_name} ({count})")
                    total_occurrences += count
            
            table_inventory.append({
                'Table Name': table,
                'Total Occurrences': total_occurrences,
                'Found in Files': len(source_files),
                'Source Files': ', '.join(source_files)
            })
        
        # Convert to DataFrame and display
        table_df = pd.DataFrame(table_inventory)
        table_df = table_df.sort_values('Total Occurrences', ascending=False)
        
        # Filter option for tables
        table_search = st.text_input("🔍 Search Tables", placeholder="Type to filter tables...")
        if table_search:
            table_df = table_df[table_df['Table Name'].str.contains(table_search, case=False, na=False)]
        
        st.dataframe(table_df, use_container_width=True)
        
        # Download button for tables
        csv_buffer = io.StringIO()
        table_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Tables Inventory (CSV)",
            data=csv_buffer.getvalue(),
            file_name="sql_tables_inventory.csv",
            mime="text/csv"
        )
    else:
        st.info("No tables found in the uploaded SQL files.")
    
    # Fields inventory
    st.subheader("🏷️ All Fields Found")
    if combined_fields:
        # Create field inventory with source files
        field_inventory = []
        for field in sorted(combined_fields):
            source_files = []
            total_occurrences = 0
            for file_name, parsed_data in all_parsed_data.items():
                if field in parsed_data.get('field_occurrences', {}):
                    count = parsed_data['field_occurrences'][field]
                    source_files.append(f"{file_name} ({count})")
                    total_occurrences += count
            
            field_inventory.append({
                'Field Name': field,
                'Total Occurrences': total_occurrences,
                'Found in Files': len(source_files),
                'Source Files': ', '.join(source_files)
            })
        
        # Convert to DataFrame and display
        field_df = pd.DataFrame(field_inventory)
        field_df = field_df.sort_values('Total Occurrences', ascending=False)
        
        # Filter and pagination options for fields
        col1, col2 = st.columns(2)
        with col1:
            field_search = st.text_input("🔍 Search Fields", placeholder="Type to filter fields...")
        with col2:
            show_top = st.selectbox("Show Top", [50, 100, 200, 500, "All"], index=0)
        
        # Apply search filter
        if field_search:
            field_df = field_df[field_df['Field Name'].str.contains(field_search, case=False, na=False)]
        
        # Apply top N filter
        if show_top != "All":
            field_df = field_df.head(int(show_top))
        
        st.dataframe(field_df, use_container_width=True)
        
        # Download button for fields
        csv_buffer = io.StringIO()
        field_df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Fields Inventory (CSV)",
            data=csv_buffer.getvalue(),
            file_name="sql_fields_inventory.csv",
            mime="text/csv"
        )
        
        # Generate standalone HTML report for SQL inventory
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📄 Generate SQL Inventory HTML Report", use_container_width=True):
                html_report = generate_sql_inventory_html_report(all_parsed_data, combined_tables, combined_fields)
                st.download_button(
                    label="📥 Download SQL Inventory HTML Report",
                    data=html_report,
                    file_name="sql_inventory_report.html",
                    mime="text/html",
                    use_container_width=True
                )
    else:
        st.info("No fields found in the uploaded SQL files.")

def display_individual_file_analysis_no_schema(all_parsed_data):
    """Display individual file analysis without schema comparison"""
    st.header("📈 Individual File Analysis")
    
    # File selector
    selected_file = st.selectbox("Select File for Detailed Analysis", list(all_parsed_data.keys()))
    
    if selected_file:
        parsed_data = all_parsed_data[selected_file]
        
        # Display file-specific information
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"🔍 Analysis for {selected_file}")
            st.write(f"**Total Statements:** {len(parsed_data['statements'])}")
            st.write(f"**Unique Tables Found:** {len(parsed_data['tables'])}")
            st.write(f"**Unique Fields Found:** {len(parsed_data['fields'])}")
            
            # Statement types
            if parsed_data['statement_types']:
                st.subheader("📊 Statement Types")
                stmt_type_data = list(parsed_data['statement_types'].items())
                stmt_type_df = pd.DataFrame(stmt_type_data)
                stmt_type_df.columns = ['Statement Type', 'Count']
                st.dataframe(stmt_type_df, use_container_width=True)
        
        with col2:
            st.subheader("🗂️ Tables and Fields Found")
            
            # Tables found
            if parsed_data['tables']:
                with st.expander(f"📋 Tables Found ({len(parsed_data['tables'])})", expanded=True):
                    tables_list = sorted(list(parsed_data['tables']))
                    for i in range(0, len(tables_list), 3):
                        cols = st.columns(3)
                        for j, table in enumerate(tables_list[i:i+3]):
                            if j < len(cols):
                                cols[j].write(f"• {table}")
            
            # Fields found
            if parsed_data['fields']:
                with st.expander(f"🏷️ Fields Found ({len(parsed_data['fields'])})", expanded=False):
                    fields_list = sorted(list(parsed_data['fields']))
                    for i in range(0, len(fields_list), 3):
                        cols = st.columns(3)
                        for j, field in enumerate(fields_list[i:i+3]):
                            if j < len(cols):
                                cols[j].write(f"• {field}")
        
        # SQL Statements Preview
        st.subheader("📝 SQL Statements Preview")
        if parsed_data['statements']:
            for i, stmt in enumerate(parsed_data['statements'][:5]):  # Show first 5 statements
                with st.expander(f"Statement {i+1}"):
                    st.code(stmt, language='sql')
            
            if len(parsed_data['statements']) > 5:
                st.info(f"Showing first 5 of {len(parsed_data['statements'])} statements")
        else:
            st.warning("No SQL statements found or parsed.")

def display_individual_file_analysis(all_parsed_data, schema_df):
    """Display individual file analysis"""
    st.header("📈 Individual File Analysis")
    
    # File selector
    selected_file = st.selectbox("Select File for Detailed Analysis", list(all_parsed_data.keys()))
    
    if selected_file:
        parsed_data = all_parsed_data[selected_file]
        
        # Analyze this specific file against schema
        analyzer = SchemaAnalyzer()
        analysis_results = analyzer.analyze(parsed_data, schema_df)
        
        # Display file-specific information
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"🔍 Analysis for {selected_file}")
            st.write(f"**Total Statements:** {len(parsed_data['statements'])}")
            st.write(f"**Unique Tables Found:** {len(parsed_data['tables'])}")
            st.write(f"**Unique Fields Found:** {len(parsed_data['fields'])}")
            
            # Statement types
            if parsed_data['statement_types']:
                st.subheader("📊 Statement Types")
                stmt_type_data = list(parsed_data['statement_types'].items())
                stmt_type_df = pd.DataFrame(stmt_type_data)
                stmt_type_df.columns = ['Statement Type', 'Count']
                st.dataframe(stmt_type_df, use_container_width=True)
        
        with col2:
            st.subheader("🗂️ Tables and Fields Found")
            
            # Tables found
            if parsed_data['tables']:
                with st.expander(f"📋 Tables Found ({len(parsed_data['tables'])})", expanded=True):
                    tables_list = sorted(list(parsed_data['tables']))
                    for i in range(0, len(tables_list), 3):
                        cols = st.columns(3)
                        for j, table in enumerate(tables_list[i:i+3]):
                            if j < len(cols):
                                cols[j].write(f"• {table}")
            
            # Fields found
            if parsed_data['fields']:
                with st.expander(f"🏷️ Fields Found ({len(parsed_data['fields'])})", expanded=False):
                    fields_list = sorted(list(parsed_data['fields']))
                    for i in range(0, len(fields_list), 3):
                        cols = st.columns(3)
                        for j, field in enumerate(fields_list[i:i+3]):
                            if j < len(cols):
                                cols[j].write(f"• {field}")
        
        # Schema comparison for this file
        st.subheader("📊 Schema Comparison for This File")
        display_comparison_report(analysis_results)
        
        # SQL Statements Preview
        st.subheader("📝 SQL Statements Preview")
        if parsed_data['statements']:
            for i, stmt in enumerate(parsed_data['statements'][:5]):  # Show first 5 statements
                with st.expander(f"Statement {i+1}"):
                    st.code(stmt, language='sql')
            
            if len(parsed_data['statements']) > 5:
                st.info(f"Showing first 5 of {len(parsed_data['statements'])} statements")
        else:
            st.warning("No SQL statements found or parsed.")

def validate_schema_format(df):
    """Validate that the schema file has required columns"""
    required_columns = ['table_name', 'field_name']
    return all(col in df.columns for col in required_columns)

def display_comparison_report(results):
    """Display the comparison report between reference schema and SQL content"""
    st.header("📊 Schema Comparison Report")
    
    comparison_data = results['comparison_report']
    
    if comparison_data.empty:
        st.warning("No comparison data available.")
        return
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_items = len(comparison_data)
    found_items = len(comparison_data[comparison_data['found'] == True])
    not_found_items = total_items - found_items
    avg_occurrences = comparison_data[comparison_data['found'] == True]['occurrences'].mean() if found_items > 0 else 0
    
    col1.metric("Total Schema Items", total_items)
    col2.metric("Found in SQL", found_items)
    col3.metric("Not Found", not_found_items)
    col4.metric("Avg Occurrences", f"{avg_occurrences:.1f}")
    
    # Detailed comparison table
    st.subheader("Detailed Comparison")
    
    # Filter options
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Found", "Not Found"])
    with filter_col2:
        table_filter = st.selectbox("Filter by Table", ["All"] + sorted(comparison_data['table_name'].unique().tolist()))
    
    # Apply filters
    filtered_data = comparison_data.copy()
    if status_filter == "Found":
        filtered_data = filtered_data[filtered_data['found'] == True]
    elif status_filter == "Not Found":
        filtered_data = filtered_data[filtered_data['found'] == False]
    
    if table_filter != "All":
        filtered_data = filtered_data[filtered_data['table_name'] == table_filter]
    
    # Style the dataframe
    def style_status(val):
        if val:
            return 'background-color: #d4edda; color: #155724'
        else:
            return 'background-color: #f8d7da; color: #721c24'
    
    styled_df = filtered_data.style.applymap(style_status, subset=['found'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Download button for comparison report
    csv_buffer = io.StringIO()
    comparison_data.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download Comparison Report (CSV)",
        data=csv_buffer.getvalue(),
        file_name="schema_comparison_report.csv",
        mime="text/csv"
    )

def display_usage_statistics(results):
    """Display usage statistics and occurrence data"""
    st.header("📈 Usage Statistics")
    
    table_stats = results['table_usage']
    field_stats = results['field_usage']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Table Usage")
        if table_stats:
            table_data = list(table_stats.items())
            table_df = pd.DataFrame(table_data, columns=['Table Name', 'Occurrences'])
            table_df = table_df.sort_values('Occurrences', ascending=False)
            st.dataframe(table_df, use_container_width=True)
            
            # Bar chart for table usage
            if len(table_df) > 0:
                st.bar_chart(table_df.set_index('Table Name')['Occurrences'])
        else:
            st.info("No table usage data available.")
    
    with col2:
        st.subheader("🏷️ Field Usage")
        if field_stats:
            field_data = list(field_stats.items())
            field_df = pd.DataFrame(field_data, columns=['Field Name', 'Occurrences'])
            field_df = field_df.sort_values('Occurrences', ascending=False)
            st.dataframe(field_df, use_container_width=True)
            
            # Bar chart for field usage (top 20)
            if len(field_df) > 0:
                top_fields = field_df.head(20)
                st.bar_chart(top_fields.set_index('Field Name')['Occurrences'])
        else:
            st.info("No field usage data available.")
    
    # Download buttons
    col1, col2 = st.columns(2)
    
    if table_stats:
        with col1:
            table_data = list(table_stats.items())
            table_csv = pd.DataFrame(table_data, columns=['Table Name', 'Occurrences']).to_csv(index=False)
            st.download_button(
                label="📥 Download Table Usage (CSV)",
                data=table_csv,
                file_name="table_usage_stats.csv",
                mime="text/csv"
            )
    
    if field_stats:
        with col2:
            field_data = list(field_stats.items())
            field_csv = pd.DataFrame(field_data, columns=['Field Name', 'Occurrences']).to_csv(index=False)
            st.download_button(
                label="📥 Download Field Usage (CSV)",
                data=field_csv,
                file_name="field_usage_stats.csv",
                mime="text/csv"
            )

def generate_html_report(all_parsed_data, combined_tables, combined_fields, schema_df):
    """Generate a comprehensive HTML report"""
    
    # Calculate summary statistics
    total_files = len(all_parsed_data)
    total_unique_tables = len(combined_tables)
    total_unique_fields = len(combined_fields)
    
    # Generate combined data for schema analysis
    combined_parsed_data = combine_all_parsed_data(all_parsed_data)
    analyzer = SchemaAnalyzer()
    analysis_results = analyzer.analyze(combined_parsed_data, schema_df)
    
    comparison_data = analysis_results['comparison_report']
    found_items = len(comparison_data[comparison_data['found'] == True]) if not comparison_data.empty else 0
    total_schema_items = len(comparison_data) if not comparison_data.empty else 0
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Schema Comparison Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
            font-style: italic;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .section {{
            margin: 40px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .section h2 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-found {{
            background-color: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status-not-found {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .file-section {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
        }}
        .file-header {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .code-block {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 SQL Schema Comparison Report</h1>
        <div class="timestamp">Generated on {timestamp}</div>
        
        <div class="summary-grid">
            <div class="metric-card">
                <div class="metric-value">{total_files}</div>
                <div class="metric-label">SQL Files Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_unique_tables}</div>
                <div class="metric-label">Unique Tables Found</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_unique_fields}</div>
                <div class="metric-label">Unique Fields Found</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{found_items}/{total_schema_items}</div>
                <div class="metric-label">Schema Items Found</div>
            </div>
        </div>
"""

    # Files and Tables Analysis Section
    html_content += """
        <div class="section">
            <h2>📁 Files & Tables Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>File Name</th>
                        <th>Table Name</th>
                        <th>Occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for file_name, parsed_data in all_parsed_data.items():
        tables = parsed_data.get('table_occurrences', {})
        if tables:
            for table, count in tables.items():
                html_content += f"""
                    <tr>
                        <td>{file_name}</td>
                        <td>{table}</td>
                        <td>{count}</td>
                    </tr>
"""
        else:
            html_content += f"""
                    <tr>
                        <td>{file_name}</td>
                        <td><em>No tables found</em></td>
                        <td>0</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
"""

    # Table Usage Summary
    html_content += """
        <div class="section">
            <h2>📋 Table Usage Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Table Name</th>
                        <th>Files Using</th>
                        <th>Total Occurrences</th>
                        <th>Files Details</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for table in sorted(combined_tables):
        files_using_table = []
        total_occurrences = 0
        for file_name, parsed_data in all_parsed_data.items():
            if table in parsed_data.get('table_occurrences', {}):
                count = parsed_data['table_occurrences'][table]
                files_using_table.append(f"{file_name} ({count})")
                total_occurrences += count
        
        html_content += f"""
                    <tr>
                        <td>{table}</td>
                        <td>{len(files_using_table)}</td>
                        <td>{total_occurrences}</td>
                        <td>{', '.join(files_using_table)}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
"""

    # Fields Analysis Section
    html_content += """
        <div class="section">
            <h2>🏷️ Field Usage Summary (Top 50)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Files Using</th>
                        <th>Total Occurrences</th>
                        <th>Files Details</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Get top 50 fields by total occurrences
    field_usage_summary = []
    for field in combined_fields:
        files_using_field = []
        total_occurrences = 0
        for file_name, parsed_data in all_parsed_data.items():
            if field in parsed_data.get('field_occurrences', {}):
                count = parsed_data['field_occurrences'][field]
                files_using_field.append(f"{file_name} ({count})")
                total_occurrences += count
        
        field_usage_summary.append({
            'field': field,
            'files_count': len(files_using_field),
            'total_occurrences': total_occurrences,
            'files_details': ', '.join(files_using_field)
        })
    
    # Sort by total occurrences and take top 50
    field_usage_summary.sort(key=lambda x: x['total_occurrences'], reverse=True)
    for field_data in field_usage_summary[:50]:
        html_content += f"""
                    <tr>
                        <td>{field_data['field']}</td>
                        <td>{field_data['files_count']}</td>
                        <td>{field_data['total_occurrences']}</td>
                        <td>{field_data['files_details']}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
"""

    # Schema Comparison Section
    if not comparison_data.empty:
        html_content += """
        <div class="section">
            <h2>📊 Schema Comparison Report</h2>
            <table>
                <thead>
                    <tr>
                        <th>Table Name</th>
                        <th>Field Name</th>
                        <th>Status</th>
                        <th>Table Found</th>
                        <th>Field Found</th>
                        <th>Total Occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for _, row in comparison_data.iterrows():
            status_class = "status-found" if row['found'] else "status-not-found"
            status_text = "Found" if row['found'] else "Not Found"
            
            html_content += f"""
                    <tr>
                        <td>{row['table_name']}</td>
                        <td>{row['field_name']}</td>
                        <td><span class="{status_class}">{status_text}</span></td>
                        <td>{'Yes' if row['table_found'] else 'No'}</td>
                        <td>{'Yes' if row['field_found'] else 'No'}</td>
                        <td>{row['occurrences']}</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
"""

    # Individual File Analysis
    html_content += """
        <div class="section">
            <h2>📈 Individual File Analysis</h2>
"""
    
    for file_name, parsed_data in all_parsed_data.items():
        html_content += f"""
            <div class="file-section">
                <div class="file-header">📄 {file_name}</div>
                <p><strong>Statements:</strong> {len(parsed_data['statements'])}</p>
                <p><strong>Tables Found:</strong> {len(parsed_data['tables'])}</p>
                <p><strong>Fields Found:</strong> {len(parsed_data['fields'])}</p>
                
                <h4>Tables in this file:</h4>
                <p>{', '.join(sorted(parsed_data['tables'])) if parsed_data['tables'] else 'No tables found'}</p>
                
                <h4>Sample SQL Statements:</h4>
"""
        
        # Show first 3 statements for each file
        for i, stmt in enumerate(parsed_data['statements'][:3]):
            html_content += f"""
                <div class="code-block">{stmt}</div>
"""
        
        if len(parsed_data['statements']) > 3:
            html_content += f"<p><em>... and {len(parsed_data['statements']) - 3} more statements</em></p>"
        
        html_content += "</div>"
    
    html_content += """
        </div>
"""

    # Footer
    html_content += f"""
        <div class="footer">
            <p>Report generated by SQL Schema Comparison Tool</p>
            <p>Analysis completed on {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def generate_sql_inventory_html_report(all_parsed_data, combined_tables, combined_fields):
    """Generate a standalone HTML report for SQL inventory only"""
    
    # Calculate summary statistics
    total_files = len(all_parsed_data)
    total_unique_tables = len(combined_tables)
    total_unique_fields = len(combined_fields)
    total_statements = sum(len(data.get('statements', [])) for data in all_parsed_data.values())
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Inventory Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
            font-style: italic;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .section {{
            margin: 40px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .section h2 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .file-section {{
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
        }}
        .file-header {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📋 SQL Inventory Report</h1>
        <div class="timestamp">Generated on {timestamp}</div>
        
        <div class="summary-grid">
            <div class="metric-card">
                <div class="metric-value">{total_files}</div>
                <div class="metric-label">SQL Files Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_unique_tables}</div>
                <div class="metric-label">Unique Tables Found</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_unique_fields}</div>
                <div class="metric-label">Unique Fields Found</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{total_statements}</div>
                <div class="metric-label">Total SQL Statements</div>
            </div>
        </div>
"""

    # Tables inventory section
    html_content += """
        <div class="section">
            <h2>📋 Complete Tables Inventory</h2>
            <table>
                <thead>
                    <tr>
                        <th>Table Name</th>
                        <th>Total Occurrences</th>
                        <th>Found in Files</th>
                        <th>Source Files</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Create table inventory
    table_inventory = []
    for table in sorted(combined_tables):
        source_files = []
        total_occurrences = 0
        for file_name, parsed_data in all_parsed_data.items():
            if table in parsed_data.get('table_occurrences', {}):
                count = parsed_data['table_occurrences'][table]
                source_files.append(f"{file_name} ({count})")
                total_occurrences += count
        
        table_inventory.append({
            'table': table,
            'total_occurrences': total_occurrences,
            'files_count': len(source_files),
            'source_files': ', '.join(source_files)
        })
    
    # Sort by total occurrences
    table_inventory.sort(key=lambda x: x['total_occurrences'], reverse=True)
    
    for table_data in table_inventory:
        html_content += f"""
                    <tr>
                        <td>{table_data['table']}</td>
                        <td>{table_data['total_occurrences']}</td>
                        <td>{table_data['files_count']}</td>
                        <td>{table_data['source_files']}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
"""

    # Fields inventory section
    html_content += """
        <div class="section">
            <h2>🏷️ Complete Fields Inventory</h2>
            <table>
                <thead>
                    <tr>
                        <th>Field Name</th>
                        <th>Total Occurrences</th>
                        <th>Found in Files</th>
                        <th>Source Files</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Create field inventory
    field_inventory = []
    for field in sorted(combined_fields):
        source_files = []
        total_occurrences = 0
        for file_name, parsed_data in all_parsed_data.items():
            if field in parsed_data.get('field_occurrences', {}):
                count = parsed_data['field_occurrences'][field]
                source_files.append(f"{file_name} ({count})")
                total_occurrences += count
        
        field_inventory.append({
            'field': field,
            'total_occurrences': total_occurrences,
            'files_count': len(source_files),
            'source_files': ', '.join(source_files)
        })
    
    # Sort by total occurrences
    field_inventory.sort(key=lambda x: x['total_occurrences'], reverse=True)
    
    for field_data in field_inventory:
        html_content += f"""
                    <tr>
                        <td>{field_data['field']}</td>
                        <td>{field_data['total_occurrences']}</td>
                        <td>{field_data['files_count']}</td>
                        <td>{field_data['source_files']}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
"""

    # Individual file breakdown
    html_content += """
        <div class="section">
            <h2>📈 File-by-File Breakdown</h2>
"""
    
    for file_name, parsed_data in all_parsed_data.items():
        html_content += f"""
            <div class="file-section">
                <div class="file-header">📄 {file_name}</div>
                <p><strong>SQL Statements:</strong> {len(parsed_data['statements'])}</p>
                <p><strong>Tables Found:</strong> {len(parsed_data['tables'])}</p>
                <p><strong>Fields Found:</strong> {len(parsed_data['fields'])}</p>
                
                <h4>Tables in this file:</h4>
                <p>{', '.join(sorted(parsed_data['tables'])) if parsed_data['tables'] else 'No tables found'}</p>
                
                <h4>All Fields in this file:</h4>
                <p>
"""
        
        # Show all fields for this file
        file_fields = parsed_data.get('field_occurrences', {})
        if file_fields:
            sorted_fields = sorted(file_fields.items(), key=lambda x: x[1], reverse=True)
            field_list = [f"{field} ({count})" for field, count in sorted_fields]
            html_content += ', '.join(field_list)
        else:
            html_content += "No fields found"
        
        html_content += """
                </p>
            </div>
"""
    
    html_content += """
        </div>
"""

    # Footer
    html_content += f"""
        <div class="footer">
            <p>SQL Inventory Report generated by SQL Schema Comparison Tool</p>
            <p>Analysis completed on {timestamp}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def generate_schema_comparison_html_report(analysis_results, schema_df, all_parsed_data):
    """Generate a dedicated HTML report for schema comparison only"""
    
    comparison_data = analysis_results['comparison_report']
    
    # Calculate summary statistics
    total_schema_items = len(comparison_data) if not comparison_data.empty else 0
    found_items = len(comparison_data[comparison_data['found'] == True]) if not comparison_data.empty else 0
    not_found_items = total_schema_items - found_items
    coverage_percentage = (found_items / total_schema_items * 100) if total_schema_items > 0 else 0
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Schema Comparison Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 10px;
            border-bottom: 3px solid #e74c3c;
            padding-bottom: 15px;
        }}
        .timestamp {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 30px;
            font-style: italic;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-card.success {{
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
        }}
        .metric-card.warning {{
            background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .section {{
            margin: 40px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #e74c3c;
        }}
        .section h2 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #34495e;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-found {{
            background-color: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .status-not-found {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}
        .schema-info {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .filter-section {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            border: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Schema Comparison Report</h1>
        <div class="timestamp">Generated on {timestamp}</div>
        
        <div class="schema-info">
            <h3>📋 Schema File Information</h3>
            <p><strong>Total Tables in Schema:</strong> {len(schema_df['table_name'].unique())}</p>
            <p><strong>Total Fields in Schema:</strong> {len(schema_df)}</p>
            <p><strong>SQL Files Analyzed:</strong> {len(all_parsed_data)}</p>
        </div>
        
        <div class="summary-grid">
            <div class="metric-card">
                <div class="metric-value">{total_schema_items}</div>
                <div class="metric-label">Schema Items to Check</div>
            </div>
            <div class="metric-card success">
                <div class="metric-value">{found_items}</div>
                <div class="metric-label">Found in SQL</div>
            </div>
            <div class="metric-card warning">
                <div class="metric-value">{not_found_items}</div>
                <div class="metric-label">Not Found</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{coverage_percentage:.1f}%</div>
                <div class="metric-label">Coverage Rate</div>
            </div>
        </div>
"""

    if not comparison_data.empty:
        # Detailed comparison section
        html_content += """
        <div class="section">
            <h2>📊 Detailed Schema Comparison</h2>
            <table>
                <thead>
                    <tr>
                        <th>Table Name</th>
                        <th>Field Name</th>
                        <th>Overall Status</th>
                        <th>Table Found in SQL</th>
                        <th>Field Found in SQL</th>
                        <th>Total Occurrences</th>
                        <th>Table Occurrences</th>
                        <th>Field Occurrences</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for _, row in comparison_data.iterrows():
            status_class = "status-found" if row['found'] else "status-not-found"
            status_text = "Found" if row['found'] else "Not Found"
            
            html_content += f"""
                    <tr>
                        <td>{row['table_name']}</td>
                        <td>{row['field_name']}</td>
                        <td><span class="{status_class}">{status_text}</span></td>
                        <td>{'Yes' if row['table_found'] else 'No'}</td>
                        <td>{'Yes' if row['field_found'] else 'No'}</td>
                        <td>{row['occurrences']}</td>
                        <td>{row['table_occurrences']}</td>
                        <td>{row['field_occurrences']}</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
"""

        # Found items summary
        found_data = comparison_data[comparison_data['found'] == True]
        if not found_data.empty:
            html_content += """
        <div class="section">
            <h2>✅ Items Found in SQL Files</h2>
            <table>
                <thead>
                    <tr>
                        <th>Table Name</th>
                        <th>Field Name</th>
                        <th>Total Occurrences</th>
                        <th>Match Type</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for _, row in found_data.iterrows():
                if row['table_found'] and row['field_found']:
                    match_type = "Both Table & Field"
                elif row['table_found']:
                    match_type = "Table Only"
                else:
                    match_type = "Field Only"
                
                html_content += f"""
                    <tr>
                        <td>{row['table_name']}</td>
                        <td>{row['field_name']}</td>
                        <td>{row['occurrences']}</td>
                        <td>{match_type}</td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
"""

        # Not found items summary
        not_found_data = comparison_data[comparison_data['found'] == False]
        if not not_found_data.empty:
            html_content += """
        <div class="section">
            <h2>❌ Items Not Found in SQL Files</h2>
            <table>
                <thead>
                    <tr>
                        <th>Table Name</th>
                        <th>Field Name</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for _, row in not_found_data.iterrows():
                html_content += f"""
                    <tr>
                        <td>{row['table_name']}</td>
                        <td>{row['field_name']}</td>
                        <td><span class="status-not-found">Missing from SQL</span></td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
"""

        # Summary by table
        html_content += """
        <div class="section">
            <h2>📋 Summary by Table</h2>
            <table>
                <thead>
                    <tr>
                        <th>Table Name</th>
                        <th>Total Fields in Schema</th>
                        <th>Fields Found in SQL</th>
                        <th>Fields Not Found</th>
                        <th>Coverage %</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        table_summary = comparison_data.groupby('table_name').agg({
            'field_name': 'count',
            'found': ['sum', lambda x: len(x) - sum(x)]
        }).round(2)
        
        for table_name in comparison_data['table_name'].unique():
            table_data = comparison_data[comparison_data['table_name'] == table_name]
            total_fields = len(table_data)
            found_fields = len(table_data[table_data['found'] == True])
            not_found_fields = total_fields - found_fields
            coverage = (found_fields / total_fields * 100) if total_fields > 0 else 0
            
            html_content += f"""
                    <tr>
                        <td>{table_name}</td>
                        <td>{total_fields}</td>
                        <td>{found_fields}</td>
                        <td>{not_found_fields}</td>
                        <td>{coverage:.1f}%</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
"""

    else:
        html_content += """
        <div class="section">
            <h2>⚠️ No Comparison Data Available</h2>
            <p>Unable to generate comparison report. Please check your schema file format and SQL files.</p>
        </div>
"""

    # Footer
    html_content += f"""
        <div class="footer">
            <p>Schema Comparison Report generated by SQL Schema Comparison Tool</p>
            <p>Analysis completed on {timestamp}</p>
            <p><strong>Note:</strong> This report shows only the comparison between your Excel schema and SQL files.</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

if __name__ == "__main__":
    main()