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
    st.markdown("Compare SQL file content against reference database schemas with occurrence tracking and comprehensive reporting.")
    
    # Sidebar for file uploads
    st.sidebar.header("📁 File Uploads")
    
    # SQL file upload
    sql_file = st.sidebar.file_uploader(
        "Upload SQL File",
        type=['sql', 'txt'],
        help="Upload your SQL file for analysis"
    )
    
    # Reference schema file upload
    schema_file = st.sidebar.file_uploader(
        "Upload Reference Schema",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel file containing table and field details"
    )
    
    if sql_file and schema_file:
        try:
            # Process SQL file
            sql_content = sql_file.read().decode('utf-8')
            parser = SQLParser()
            parsed_data = parser.parse_sql(sql_content)
            
            # Process schema file
            if schema_file.name.endswith('.csv'):
                schema_df = pd.read_csv(schema_file)
            else:
                schema_df = pd.read_excel(schema_file)
            
            # Validate schema format
            if not validate_schema_format(schema_df):
                st.error("❌ Invalid schema file format. Please ensure your file has 'table_name' and 'field_name' columns.")
                return
            
            # Analyze schema
            analyzer = SchemaAnalyzer()
            analysis_results = analyzer.analyze(parsed_data, schema_df)
            
            # Display results in tabs
            tab1, tab2, tab3 = st.tabs(["📊 Comparison Report", "📈 Usage Statistics", "📋 SQL Content Analysis"])
            
            with tab1:
                display_comparison_report(analysis_results)
            
            with tab2:
                display_usage_statistics(analysis_results)
            
            with tab3:
                display_sql_analysis(parsed_data, analysis_results)
                
        except Exception as e:
            st.error(f"❌ Error processing files: {str(e)}")
            st.info("Please check your file formats and try again.")
    
    elif sql_file and not schema_file:
        st.warning("⚠️ Please upload a reference schema file to perform comparison.")
    elif schema_file and not sql_file:
        st.warning("⚠️ Please upload a SQL file for analysis.")
    else:
        st.info("👆 Please upload both SQL file and reference schema file to begin analysis.")
        
        # Display help information
        with st.expander("ℹ️ How to use this tool"):
            st.markdown("""
            ### SQL File Requirements:
            - Supported formats: `.sql`, `.txt`
            - Should contain valid SQL statements
            - Supports multiple SQL dialects (MySQL, PostgreSQL, SQL Server, etc.)
            
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
            table_df = pd.DataFrame(list(table_stats.items()), columns=['Table Name', 'Occurrences'])
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
            field_df = pd.DataFrame(list(field_stats.items()), columns=['Field Name', 'Occurrences'])
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
            table_csv = pd.DataFrame(list(table_stats.items()), columns=['Table Name', 'Occurrences']).to_csv(index=False)
            st.download_button(
                label="📥 Download Table Usage (CSV)",
                data=table_csv,
                file_name="table_usage_stats.csv",
                mime="text/csv"
            )
    
    if field_stats:
        with col2:
            field_csv = pd.DataFrame(list(field_stats.items()), columns=['Field Name', 'Occurrences']).to_csv(index=False)
            st.download_button(
                label="📥 Download Field Usage (CSV)",
                data=field_csv,
                file_name="field_usage_stats.csv",
                mime="text/csv"
            )

def display_sql_analysis(parsed_data, results):
    """Display SQL content analysis"""
    st.header("📋 SQL Content Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 SQL Parsing Summary")
        st.write(f"**Total Statements:** {len(parsed_data['statements'])}")
        st.write(f"**Unique Tables Found:** {len(parsed_data['tables'])}")
        st.write(f"**Unique Fields Found:** {len(parsed_data['fields'])}")
        
        # Statement types
        if parsed_data['statement_types']:
            st.subheader("📊 Statement Types")
            stmt_type_df = pd.DataFrame(list(parsed_data['statement_types'].items()), 
                                      columns=['Statement Type', 'Count'])
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

if __name__ == "__main__":
    main()
