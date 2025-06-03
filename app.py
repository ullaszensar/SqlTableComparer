import streamlit as st
import pandas as pd
import io
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
            tab1, tab2, tab3, tab4 = st.tabs([
                "📁 Files & Tables Analysis", 
                "📋 Files & Fields Analysis", 
                "📊 Schema Comparison", 
                "📈 Individual File Analysis"
            ])
            
            with tab1:
                display_files_tables_analysis(all_parsed_data, combined_tables)
            
            with tab2:
                display_files_fields_analysis(all_parsed_data, combined_fields)
            
            with tab3:
                # Create combined data for schema comparison
                combined_parsed_data = combine_all_parsed_data(all_parsed_data)
                analyzer = SchemaAnalyzer()
                analysis_results = analyzer.analyze(combined_parsed_data, schema_df)
                display_comparison_report(analysis_results)
            
            with tab4:
                display_individual_file_analysis(all_parsed_data, schema_df)
                
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
            st.info("Please check your file formats and try again.")
    
    elif sql_files and not schema_file:
        st.warning("⚠️ Please upload a reference schema file to perform comparison.")
    elif schema_file and not sql_files:
        st.warning("⚠️ Please upload SQL files for analysis.")
    else:
        st.info("👆 Please upload both SQL files and reference schema file to begin analysis.")
        
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

if __name__ == "__main__":
    main()