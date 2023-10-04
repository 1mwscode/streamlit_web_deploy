# 라이브러리
import ast
import folium
import pandas as pd
import geopandas as gpd
import streamlit as st
from st_aggrid import AgGrid
from streamlit_folium import folium_static
from folium import GeoJson
import plotly.express as px
from folium.vector_layers import Polygon
from shapely.geometry import Polygon

# 한글깨짐 해결
from matplotlib import rc
import matplotlib.pyplot as plt
rc('font', family='AppleGothic')
plt.rcParams['axes.unicode_minus'] = False

def display_state_filter(df):
    state_list = sorted(df['sig_kor_nm'].unique())
    selected_states = st.sidebar.multiselect('지역을 선택하세요', state_list, default=["창녕군"])   # state_list
    return selected_states

def display_livestock_filter(df): 
    livestock_list = ['전체'] + sorted(df['prt_type_nm'].unique())
    selected_livestocks = st.sidebar.multiselect('축사 종류를 선택하세요', livestock_list, default=['전체'])
    st.header(f'{"📍"+"· ".join(selected_livestocks)} 축사 위치')
    st.caption("사이드바에서 선택한 축사만 표출됩니다.")
    return selected_livestocks

def display_map(df, selected_states, selected_livestocks, color_mapping):
    if selected_states:
        df = df[df['sig_kor_nm'].isin(selected_states)]
    
    if '전체' not in selected_livestocks:
        df = df[df['prt_type_nm'].isin(selected_livestocks)]

    if not df.empty:
        df['geometry'] = df['geom_coordinates'].apply(lambda x: Polygon(ast.literal_eval(x)[0]) if pd.notnull(x) else None)

        # GeoDataFrame의 중심 계산
        center_lat = df['geometry'].centroid.y.mean()
        center_lon = df['geometry'].centroid.x.mean()
        map = folium.Map(location=[center_lat, center_lon], zoom_start=13, scrollWheelZoom=False, tiles='CartoDB positron')

        selected_livestocks = ['닭', '돼지', '소', 'Unknown']
        for property_type_name in selected_livestocks:
            subset_df = df[df['prt_type_nm'] == property_type_name]
            for _, row in subset_df.iterrows():
                if row['geometry'] is not None and row['geometry'].is_valid:
                    folium.GeoJson(row['geometry'],
                                style_function=lambda x, color=color_mapping.get(property_type_name, 'gray'):{'color': color, 'fillColor':color}).add_to(map)
        folium_static(map)

    else :
        map = folium.Map(location=[36.9347224, 127.8719619], zoom_start=10, scrollWheelZoom=False, tiles='CartoDB positron')
    return map


    
    # 변수선언 및 초기화
    renamed_df_show = None

    if selected_states:
        df = df[df['sig_kor_nm'].isin(selected_states)]
    
    if '전체' not in selected_livestocks:
        df = df[df['prt_type_nm'].isin(selected_livestocks)]
        renamed_df = df.rename(columns={
            'sig_kor_nm': '지역 이름',
            'prt_type_nm': '축사 종류',
            'geom_coordinates': '좌표'
        })

        renamed_df.reset_index(drop= True, inplace = True)
        renamed_df.index += 1
        renamed_df_show = renamed_df[["지역 이름", "축사 종류", "좌표"]]
    else:
        renamed_df_show = df[["sig_kor_nm", "prt_type_nm", "geom_coordinates"]]
    st.table(renamed_df_show)

def display_statistics_and_graph(df, selected_states, selected_livestocks, color_mapping):
    if selected_states:
        df = df[df['sig_kor_nm'].isin(selected_states)]

    if '전체' not in selected_livestocks:
        df = df[df['prt_type_nm'].isin(selected_livestocks)]
    
    # 데이터 프레임에서 'SIG_KOR_NM'과 'property_type_name'으로 그룹화하고 갯수 세기
    grouped_df = df.groupby(['sig_kor_nm', 'prt_type_nm']).size().reset_index(name='count')
    
    if not grouped_df.empty:
        fig = px.bar(grouped_df, x='count', y='sig_kor_nm', color='prt_type_nm', 
                orientation='h', 
                labels={'sig_kor_nm':'지역명', 'count':'축사 수', 'prt_type_nm':'축사 종류'},
                title='지역별 축사현황 차트',
                color_discrete_map= color_mapping)
        
        fig2 = px.pie(grouped_df, values='count', names='prt_type_nm', 
                 color='prt_type_nm',
                 labels={'count':'축사 수', 'prt_type_nm':'축사 종류'},
                 hole =0.2,
                 title='축사별 현황 차트',
                 color_discrete_map=color_mapping)
    
        cols = st.columns(2)
        cols[0].plotly_chart(fig, use_container_width= True)
        cols[1].plotly_chart(fig2, use_container_width= True)

    else :
        st.warning('No data available for the selected regions and livestocks.')
    
    # 통계 정보 출력
    st.markdown("**통계정보**")
    re_grouped_df = grouped_df.rename(columns={'sig_kor_nm': '지역명',
                                               'prt_type_nm': '축사 종류',
                                               'geom_coordinates': '좌표',
                                               'count' : '축사 수', 
                                               }
                                    )
    re_grouped_df.reset_index(drop=True, inplace=True)
    re_grouped_df.index += 1
    st.table(re_grouped_df)
    # AgGrid(re_grouped_df, fill_width=True)

def display_filtered_table(df, selected_states, selected_livestocks):
    renamed_df_show = None     # 초기값 설정

    if selected_states:
        df = df[df['sig_kor_nm'].isin(selected_states)]
    if '전체' not in selected_livestocks:
        df = df[df['prt_type_nm'].isin(selected_livestocks)]

    # 웹에 표출되는 columns값 변경하여 표출
    renamed_df = df.rename(columns={'sig_kor_nm': '지역명',
                                    'prt_type_nm': '축사 종류',
                                    'geom_coordinates': '좌표'
                                    }
                            )
    renamed_df.reset_index(drop=True, inplace=True)
    renamed_df.index += 1
    renamed_df_show = renamed_df[["지역명", "축사 종류", "좌표"]] # 필요한 정보만 표출하기

    show_full_data = st.checkbox("선택된 데이터 확인", False)
    if show_full_data:
        AgGrid(renamed_df_show)  # 원본 데이터 표시

def main():
    # 기본정보
    APP_TITLE = '대한민국 축사현황 정보판'
    st.title(APP_TITLE)
    st.caption("""대한민국 축사현황 정보판은 아리랑 3호(K3)의 고해상도 위성영상 데이터를 활용한 라벨링 데이터를 바탕으로 작성한 대시보드입니다. 
               사용자는 좌측 사이드바의 원하는 지역 및 축사 종류를 선택함으로써, 지역별 축사 분포 및 특성에 대한 상세한 통계 정보을 파악할 수 있습니다. 
               """)

    # 가축별 색상설정
    color_mapping = {'Unknown': '#090707',   # 검은색
                     '닭': '#EFDC05',        # 노란색
                     '돼지': '#E53A40',      # 빨간색
                     '소': '#30A9DE',       # 파란
                     }

    # 데이터 경로
    df_gpd = gpd.read_file('./data/db/results/livestocks.db', encoding ='utf-8')
    df = pd.DataFrame(df_gpd.drop(columns=['geometry']))  # geometry 열을 제거하는 경우

    # 지역 및 축사 선택하여 선택한 축사 지도로 표출
    st.sidebar.title('지역 및 축사종류 선택')
    selected_states = display_state_filter(df_gpd)
    selected_livestocks = display_livestock_filter(df_gpd)
    display_map(df_gpd, selected_states, selected_livestocks,color_mapping)

    # 통계차트 및 원본데이터 표출
    display_statistics_and_graph(df, selected_states, selected_livestocks,color_mapping)
    display_filtered_table(df, selected_states, selected_livestocks)

    # 기본정보
    APP_SUB_TITLE = 'Copyright © 2023. MOONSOFT, All rights reserved.'
    st.caption(APP_SUB_TITLE)

if __name__ == "__main__":
    main()
