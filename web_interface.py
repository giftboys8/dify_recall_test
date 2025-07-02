#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify知识库召回测试 - Web界面
使用Streamlit提供图形化测试界面
"""

import streamlit as st
import pandas as pd
import json
import io
import time
from datetime import datetime
from enhanced_recall_tester import (
    EnhancedDifyRecallTester, 
    TestConfig, 
    TestCase, 
    load_test_cases_from_csv
)
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 页面配置
st.set_page_config(
    page_title="Dify知识库召回测试",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.success-metric {
    background-color: #d4edda;
    border-left: 4px solid #28a745;
}
.error-metric {
    background-color: #f8d7da;
    border-left: 4px solid #dc3545;
}
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """初始化会话状态"""
    if 'test_results' not in st.session_state:
        st.session_state.test_results = []
    if 'test_config' not in st.session_state:
        st.session_state.test_config = None
    if 'test_cases' not in st.session_state:
        st.session_state.test_cases = []

def create_config_form():
    """创建配置表单"""
    st.sidebar.header("🔧 API配置")
    
    with st.sidebar.form("config_form"):
        api_url = st.text_input(
            "API基础URL", 
            value="https://api.dify.ai",
            help="Dify API的基础URL"
        )
        
        api_key = st.text_input(
            "API密钥", 
            type="password",
            help="您的Dify API密钥"
        )
        
        dataset_id = st.text_input(
            "知识库ID", 
            help="要测试的知识库ID"
        )
        
        st.subheader("测试参数")
        
        col1, col2 = st.columns(2)
        with col1:
            top_k = st.number_input("返回文档数量", min_value=1, max_value=50, value=10)
            delay = st.number_input("请求间隔(秒)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
        
        with col2:
            reranking_enabled = st.checkbox("启用重排序", value=True)
            score_threshold_enabled = st.checkbox("启用分数阈值", value=False)
        
        if score_threshold_enabled:
            score_threshold = st.slider("分数阈值", 0.0, 1.0, 0.5, 0.01)
        else:
            score_threshold = 0.0
        
        submitted = st.form_submit_button("保存配置")
        
        if submitted and api_key and dataset_id:
            config = TestConfig(
                api_base_url=api_url,
                api_key=api_key,
                dataset_id=dataset_id,
                top_k=top_k,
                delay_between_requests=delay,
                reranking_enabled=reranking_enabled,
                score_threshold_enabled=score_threshold_enabled,
                score_threshold=score_threshold
            )
            st.session_state.test_config = config
            st.sidebar.success("✅ 配置已保存")
        elif submitted:
            st.sidebar.error("❌ 请填写完整的API配置")

def upload_test_cases():
    """上传测试用例"""
    st.header("📁 测试用例管理")
    
    tab1, tab2 = st.tabs(["上传CSV文件", "手动添加"])
    
    with tab1:
        uploaded_file = st.file_uploader(
            "选择测试用例CSV文件",
            type=['csv'],
            help="CSV文件应包含列: id, query, category, description"
        )
        
        if uploaded_file is not None:
            try:
                # 保存上传的文件
                with open("temp_test_cases.csv", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 加载测试用例
                test_cases = load_test_cases_from_csv("temp_test_cases.csv")
                st.session_state.test_cases = test_cases
                
                st.success(f"✅ 成功加载 {len(test_cases)} 个测试用例")
                
                # 显示预览
                df = pd.DataFrame([{
                    'ID': tc.id,
                    '查询': tc.query,
                    '分类': tc.category,
                    '描述': tc.description
                } for tc in test_cases])
                
                st.dataframe(df, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ 文件加载失败: {str(e)}")
    
    with tab2:
        with st.form("manual_test_case"):
            col1, col2 = st.columns(2)
            
            with col1:
                test_id = st.text_input("测试ID")
                query = st.text_area("查询文本", height=100)
            
            with col2:
                category = st.text_input("分类")
                description = st.text_area("描述", height=100)
            
            if st.form_submit_button("添加测试用例"):
                if test_id and query:
                    new_case = TestCase(
                        id=test_id,
                        query=query,
                        category=category,
                        description=description
                    )
                    st.session_state.test_cases.append(new_case)
                    st.success("✅ 测试用例已添加")
                    st.rerun()
                else:
                    st.error("❌ 请填写测试ID和查询文本")

def run_tests():
    """运行测试"""
    st.header("🚀 执行测试")
    
    if not st.session_state.test_config:
        st.warning("⚠️ 请先在侧边栏配置API参数")
        return
    
    if not st.session_state.test_cases:
        st.warning("⚠️ 请先上传或添加测试用例")
        return
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write(f"准备测试 {len(st.session_state.test_cases)} 个用例")
    
    with col2:
        if st.button("🚀 开始测试", type="primary"):
            run_batch_test()
    
    with col3:
        if st.button("🗑️ 清除结果"):
            st.session_state.test_results = []
            st.rerun()

def run_batch_test():
    """执行批量测试"""
    tester = EnhancedDifyRecallTester(st.session_state.test_config)
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    total_cases = len(st.session_state.test_cases)
    
    for i, test_case in enumerate(st.session_state.test_cases):
        status_text.text(f"正在测试: {test_case.id} - {test_case.query[:50]}...")
        
        result = tester.test_single_query(test_case)
        results.append(result)
        
        progress_bar.progress((i + 1) / total_cases)
        
        # 添加延迟
        if i < total_cases - 1:
            time.sleep(st.session_state.test_config.delay_between_requests)
    
    st.session_state.test_results = results
    status_text.text("✅ 测试完成！")
    
    # 显示结果摘要
    successful_tests = [r for r in results if r.success]
    st.success(f"测试完成！成功: {len(successful_tests)}, 失败: {len(results) - len(successful_tests)}")

def display_results():
    """显示测试结果"""
    if not st.session_state.test_results:
        return
    
    st.header("📊 测试结果")
    
    results = st.session_state.test_results
    successful_results = [r for r in results if r.success]
    
    # 总体统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总测试数", len(results))
    
    with col2:
        st.metric("成功数", len(successful_results))
    
    with col3:
        success_rate = len(successful_results) / len(results) * 100 if results else 0
        st.metric("成功率", f"{success_rate:.1f}%")
    
    with col4:
        if successful_results:
            avg_time = sum(r.response_time for r in successful_results) / len(successful_results)
            st.metric("平均响应时间", f"{avg_time:.2f}s")
    
    # 详细结果表格
    st.subheader("详细结果")
    
    # 创建结果DataFrame
    result_data = []
    for result in results:
        scores = result.scores if result.success else []
        result_data.append({
            '测试ID': result.test_id,
            '查询': result.query[:50] + '...' if len(result.query) > 50 else result.query,
            '分类': result.category,
            '状态': '✅ 成功' if result.success else '❌ 失败',
            '文档数': len(result.documents),
            '最高分数': max(scores) if scores else 0,
            '平均分数': sum(scores) / len(scores) if scores else 0,
            '响应时间': f"{result.response_time:.2f}s",
            '错误信息': result.error_message if not result.success else ''
        })
    
    df = pd.DataFrame(result_data)
    st.dataframe(df, use_container_width=True)
    
    # 可视化图表
    if successful_results:
        display_visualizations(successful_results)
    
    # 下载结果
    st.subheader("📥 下载结果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV下载
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📄 下载CSV",
            data=csv_buffer.getvalue(),
            file_name=f"recall_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # JSON下载
        json_data = [{
            'test_id': r.test_id,
            'query': r.query,
            'category': r.category,
            'success': r.success,
            'scores': r.scores,
            'documents': r.documents,
            'response_time': r.response_time,
            'timestamp': r.timestamp,
            'error_message': r.error_message
        } for r in results]
        
        st.download_button(
            label="📋 下载JSON",
            data=json.dumps(json_data, ensure_ascii=False, indent=2),
            file_name=f"recall_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def display_visualizations(successful_results):
    """显示可视化图表"""
    st.subheader("📈 数据可视化")
    
    # 收集数据
    all_scores = [score for result in successful_results for score in result.scores]
    
    if not all_scores:
        st.warning("没有分数数据可供可视化")
        return
    
    tab1, tab2, tab3 = st.tabs(["分数分布", "分类分析", "性能分析"])
    
    with tab1:
        # 分数分布直方图
        fig = px.histogram(
            x=all_scores,
            nbins=30,
            title="召回分数分布",
            labels={'x': '分数', 'y': '频次'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # 分数统计
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("最高分数", f"{max(all_scores):.3f}")
        with col2:
            st.metric("最低分数", f"{min(all_scores):.3f}")
        with col3:
            st.metric("平均分数", f"{sum(all_scores)/len(all_scores):.3f}")
    
    with tab2:
        # 按分类统计
        category_data = {}
        for result in successful_results:
            if result.category and result.scores:
                if result.category not in category_data:
                    category_data[result.category] = []
                category_data[result.category].extend(result.scores)
        
        if category_data:
            categories = list(category_data.keys())
            avg_scores = [sum(scores)/len(scores) for scores in category_data.values()]
            
            fig = px.bar(
                x=categories,
                y=avg_scores,
                title="各分类平均召回分数",
                labels={'x': '分类', 'y': '平均分数'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("没有分类数据可供分析")
    
    with tab3:
        # 响应时间分析
        response_times = [r.response_time for r in successful_results]
        
        fig = px.histogram(
            x=response_times,
            nbins=20,
            title="响应时间分布",
            labels={'x': '响应时间 (秒)', 'y': '频次'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 文档数量分布
        doc_counts = [len(r.documents) for r in successful_results]
        
        fig = px.histogram(
            x=doc_counts,
            title="召回文档数量分布",
            labels={'x': '文档数量', 'y': '频次'}
        )
        st.plotly_chart(fig, use_container_width=True)

def main():
    """主函数"""
    st.title("🔍 Dify知识库召回测试工具")
    st.markdown("---")
    
    # 初始化会话状态
    init_session_state()
    
    # 侧边栏配置
    create_config_form()
    
    # 主要内容区域
    upload_test_cases()
    st.markdown("---")
    run_tests()
    st.markdown("---")
    display_results()
    
    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>""Dify知识库召回测试工具 | 支持批量测试和结果分析""</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()