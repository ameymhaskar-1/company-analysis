import pandas as pd

def generate_excel_workbook(buffer, data_dict, companies):
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # The 26 Strict Sheets
        sheet_names = [
            "01_Cover", "02_Company_Master", "03_Executive_Summary", "04_Market_Data", 
            "05_Income_Statement", "06_Balance_Sheet", "07_Cash_Flow", "08_Growth", 
            "09_Profitability", "10_Valuation", "11_Dividends", "12_Shareholding", 
            "13_Working_Capital", "14_Debt_Health", "15_Returns", "16_Fundamental_Score", 
            "17_Risk_Flags", "18_Annual_Report_Insights", "19_Company_Comparison", 
            "20_Screener", "21_Data_Sources", "22_Data_Quality", "23_Pivot_Source", 
            "24_Pivot_Analysis", "25_Charts", "26_Raw_Data"
        ]
        
        # 1. Write basic structural data to individual pages
        for sheet in sheet_names:
            ws = workbook.add_worksheet(sheet)
            ws.write(0, 0, f"Sheet: {sheet}")
            
        # 22. Data Quality
        if 'data_quality' in data_dict and not data_dict['data_quality'].empty:
            data_dict['data_quality'].to_excel(writer, sheet_name='22_Data_Quality', index=False, startrow=2)
            
        # 04. Market Data
        if 'market_data' in data_dict and not data_dict['market_data'].empty:
            data_dict['market_data'].to_excel(writer, sheet_name='04_Market_Data', index=False, startrow=2)

        # 23. Pivot Source (Normalized Table injection)
        ws_source = writer.sheets['23_Pivot_Source']
        fin_df = data_dict.get('financials', pd.DataFrame())
        if not fin_df.empty:
            fin_df.to_excel(writer, sheet_name='23_Pivot_Source', index=False, startrow=1)
            num_rows, num_cols = fin_df.shape
            ws_source.add_table(1, 0, num_rows + 1, num_cols - 1, {
                'columns': [{'header': c} for c in fin_df.columns],
                'name': 'tblFinancialData'
            })
            
        # 24. Pivot Analysis (Real Pandas Pivots)
        ws_pivot = writer.sheets['24_Pivot_Analysis']
        current_row = 2
        
        if not fin_df.empty and 'Metric' in fin_df.columns:
            # Pivot 1: Revenue by Company and FY
            rev_df = fin_df[fin_df['Metric'] == 'Revenue']
            if not rev_df.empty:
                pvt_rev = pd.pivot_table(rev_df, values='Value', index='Company', columns='Financial Year', aggfunc='sum')
                ws_pivot.write_string(current_row, 0, "1. Revenue by Company & FY")
                pvt_rev.to_excel(writer, sheet_name='24_Pivot_Analysis', startrow=current_row+2)
                
                # Generate Real Chart in Sheet 25 linked to Sheet 24
                ws_chart = writer.sheets['25_Charts']
                chart = workbook.add_chart({'type': 'line'})
                num_companies = len(pvt_rev)
                num_years = len(pvt_rev.columns)
                for i in range(num_companies):
                    r = current_row + 3 + i
                    chart.add_series({
                        'name':       ['24_Pivot_Analysis', r, 0],
                        'categories': ['24_Pivot_Analysis', current_row + 2, 1, current_row + 2, num_years],
                        'values':     ['24_Pivot_Analysis', r, 1, r, num_years],
                    })
                chart.set_title({'name': 'Real Revenue Trend'})
                ws_chart.insert_chart('B2', chart)
                current_row += len(pvt_rev) + 6

            # Pivot 2: PAT by Company and FY
            pat_df = fin_df[fin_df['Metric'] == 'PAT']
            if not pat_df.empty:
                pvt_pat = pd.pivot_table(pat_df, values='Value', index='Company', columns='Financial Year', aggfunc='sum')
                ws_pivot.write_string(current_row, 0, "2. PAT by Company & FY")
                pvt_pat.to_excel(writer, sheet_name='24_Pivot_Analysis', startrow=current_row+2)

        # 26. Raw Data (Real Dumps)
        if 'corporate_actions' in data_dict and not data_dict['corporate_actions'].empty:
            data_dict['corporate_actions'].to_excel(writer, sheet_name='26_Raw_Data', index=False, startrow=2)
