<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis readOnly="0" version="3.4.12-Madeira" hasScaleBasedVisibilityFlag="0" minScale="1e+08" styleCategories="AllStyleCategories" labelsEnabled="0" simplifyMaxScale="1" simplifyLocal="1" maxScale="0" simplifyDrawingHints="0" simplifyDrawingTol="1" simplifyAlgorithm="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" enableorderby="0" type="graduatedSymbol" forceraster="0" attr="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" graduatedMethod="GraduatedColor">
    <ranges>
      <range render="false" lower="0.000000000000000" upper="0.027909595519304" symbol="0" label="0.00 - 0.03"/>
      <range render="false" lower="0.027909595519304" upper="0.251259861539944" symbol="1" label="0.03 - 0.25"/>
      <range render="false" lower="0.251259861539944" upper="0.658597621917724" symbol="2" label="0.25 - 0.66"/>
      <range render="false" lower="0.658597621917724" upper="1.306923360036244" symbol="3" label="0.66 - 1.31"/>
      <range render="false" lower="1.306923360036244" upper="2.198520047500671" symbol="4" label="1.31 - 2.20"/>
      <range render="false" lower="2.198520047500671" upper="3.683489033353232" symbol="5" label="2.20 - 3.68"/>
      <range render="false" lower="3.683489033353232" upper="5.855237806778824" symbol="6" label="3.68 - 5.86"/>
      <range render="false" lower="5.855237806778824" upper="9.196722277286291" symbol="7" label="5.86 - 9.20"/>
      <range render="false" lower="9.196722277286291" upper="14.200039624406985" symbol="8" label="9.20 - 14.20"/>
      <range render="false" lower="14.200039624406985" upper="20.419054402120569" symbol="9" label="14.20 - 20.42"/>
      <range render="true" lower="20.419054402120569" upper="27.944217097396105" symbol="10" label="20.42 - 27.94"/>
      <range render="true" lower="27.944217097396105" upper="37.892228434154916" symbol="11" label="27.94 - 37.89"/>
      <range render="true" lower="37.892228434154916" upper="50.423237510429246" symbol="12" label="37.89 - 50.42"/>
      <range render="true" lower="50.423237510429246" upper="67.579575024190476" symbol="13" label="50.42 - 67.58"/>
      <range render="true" lower="67.579575024190476" upper="88.238661426887049" symbol="14" label="67.58 - 88.24"/>
      <range render="true" lower="88.238661426887049" upper="119.967620013501147" symbol="15" label="88.24 - 119.97"/>
      <range render="true" lower="119.967620013501147" upper="166.582416660404078" symbol="16" label="119.97 - 166.58"/>
      <range render="true" lower="166.582416660404078" upper="233.863904853356274" symbol="17" label="166.58 - 233.86"/>
      <range render="true" lower="233.863904853356274" upper="305.142909463155661" symbol="18" label="233.86 - 305.14"/>
      <range render="true" lower="305.142909463155661" upper="395.375141898572508" symbol="19" label="305.14 - 395.38"/>
      <range render="true" lower="395.375141898572508" upper="497.679323779119841" symbol="20" label="395.38 - 497.68"/>
      <range render="true" lower="497.679323779119841" upper="593.689486004241871" symbol="21" label="497.68 - 593.69"/>
      <range render="true" lower="593.689486004241871" upper="751.120782947572820" symbol="22" label="593.69 - 751.12"/>
      <range render="true" lower="751.120782947572820" upper="961.639247847240995" symbol="23" label="751.12 - 961.64"/>
      <range render="true" lower="961.639247847240995" upper="1630.915223158349136" symbol="24" label="961.64 - 1630.92"/>
    </ranges>
    <symbols>
      <symbol alpha="1" force_rhr="0" name="0" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="247,251,255,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="1" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="239,246,253,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="10" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="148,197,223,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="11" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="131,188,220,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="12" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="115,179,216,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="13" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="100,169,212,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="14" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="87,160,207,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="15" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="74,151,201,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="16" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="62,142,196,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="17" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="51,131,191,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="18" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="40,121,185,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="19" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="30,110,179,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="2" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="231,241,250,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="20" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="21,99,170,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="21" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="13,88,161,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="22" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="8,75,148,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="23" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="8,61,127,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="24" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="8,48,107,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="3" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="223,236,248,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="4" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="216,231,245,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="5" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="208,226,243,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="6" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="200,221,240,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="7" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="188,215,236,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="8" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="176,210,232,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" force_rhr="0" name="9" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="163,204,227,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <source-symbol>
      <symbol alpha="1" force_rhr="0" name="0" type="marker" clip_to_extent="1">
        <layer locked="0" pass="0" enabled="1" class="SvgMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="0,0,0,255"/>
          <prop k="fixedAspectRatio" v="2"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v="arrows/Arrow_05.svg"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties" type="Map">
                <Option name="angle" type="Map">
                  <Option name="active" type="bool" value="true"/>
                  <Option name="expression" type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))"/>
                  <Option name="type" type="int" value="3"/>
                </Option>
              </Option>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </source-symbol>
    <colorramp name="[source]" type="gradient">
      <prop k="color1" v="247,251,255,255"/>
      <prop k="color2" v="8,48,107,255"/>
      <prop k="discrete" v="0"/>
      <prop k="rampType" v="gradient"/>
      <prop k="stops" v="0.13;222,235,247,255:0.26;198,219,239,255:0.39;158,202,225,255:0.52;107,174,214,255:0.65;66,146,198,255:0.78;33,113,181,255:0.9;8,81,156,255"/>
    </colorramp>
    <mode name="quantile"/>
    <symmetricMode astride="false" enabled="false" symmetryPoint="0"/>
    <rotation/>
    <sizescale/>
    <labelformat trimtrailingzeroes="false" decimalplaces="2" format="%1 - %2"/>
  </renderer-v2>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames">
      <value>vfr_metres_to_unit</value>
      <value>vfr_scale</value>
    </property>
    <property key="variableValues">
      <value>1.9349746982808556</value>
      <value>1.0</value>
    </property>
    <property key="vfr_scale_group" value=""/>
    <property key="vfr_scale_group_factor" value="1"/>
    <property key="vfr_settings" value="{&quot;arrowAngleDegrees&quot;: false, &quot;arrowAngleFromNorth&quot;: true, &quot;arrowBorderColor&quot;: &quot;#ff000000&quot;, &quot;arrowBorderWidth&quot;: 0.0, &quot;arrowFillColor&quot;: &quot;#ff000000&quot;, &quot;arrowHeadRelativeLength&quot;: 1.5, &quot;arrowHeadWidth&quot;: 3.0, &quot;arrowMaxRelativeHeadSize&quot;: 0.3, &quot;arrowMode&quot;: &quot;xy&quot;, &quot;arrowShaftWidth&quot;: 0.75, &quot;baseBorderColor&quot;: &quot;#ff000000&quot;, &quot;baseBorderWidth&quot;: 0.0, &quot;baseFillColor&quot;: &quot;#ffff0000&quot;, &quot;baseSize&quot;: 2.0, &quot;drawArrow&quot;: true, &quot;drawEllipse&quot;: true, &quot;drawEllipseAxes&quot;: false, &quot;dxField&quot;: &quot;q_out_x_sum&quot;, &quot;dyField&quot;: &quot;q_out_y_sum&quot;, &quot;ellipseAngleFromNorth&quot;: true, &quot;ellipseBorderColor&quot;: &quot;#ff000000&quot;, &quot;ellipseBorderWidth&quot;: 0.7, &quot;ellipseDegrees&quot;: true, &quot;ellipseFillColor&quot;: &quot;#ff000000&quot;, &quot;ellipseMode&quot;: &quot;axes&quot;, &quot;ellipseScale&quot;: 1.0, &quot;ellipseTickSize&quot;: 2.0, &quot;emaxAzimuthField&quot;: &quot;&quot;, &quot;emaxField&quot;: &quot;&quot;, &quot;eminField&quot;: &quot;&quot;, &quot;fillArrow&quot;: true, &quot;fillBase&quot;: true, &quot;fillEllipse&quot;: false, &quot;scale&quot;: 1.0, &quot;scaleGroup&quot;: &quot;&quot;, &quot;scaleGroupFactor&quot;: 1.0, &quot;scaleIsMetres&quot;: false, &quot;symbolRenderUnit&quot;: &quot;mm&quot;}"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory lineSizeType="MM" sizeScale="3x:0,0,0,0,0,0" scaleDependency="Area" width="15" rotationOffset="270" height="15" lineSizeScale="3x:0,0,0,0,0,0" labelPlacementMethod="XHeight" penWidth="0" minimumSize="0" minScaleDenominator="0" enabled="0" opacity="1" scaleBasedVisibility="0" backgroundAlpha="255" sizeType="MM" diagramOrientation="Up" backgroundColor="#ffffff" penAlpha="255" maxScaleDenominator="1e+08" penColor="#000000" barWidth="5">
      <fontProperties style="" description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0"/>
      <attribute field="" color="#000000" label=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings obstacle="0" priority="0" dist="0" linePlacementFlags="18" placement="0" zIndex="0" showAll="1">
    <properties>
      <Option type="Map">
        <Option name="name" type="QString" value=""/>
        <Option name="properties"/>
        <Option name="type" type="QString" value="collection"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="q_out_x_sum">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="q_out_y_sum">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="q_out_x_sum" name="" index="0"/>
    <alias field="q_out_y_sum" name="" index="1"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="q_out_x_sum" expression="" applyOnUpdate="0"/>
    <default field="q_out_y_sum" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint field="q_out_x_sum" notnull_strength="0" unique_strength="0" constraints="0" exp_strength="0"/>
    <constraint field="q_out_y_sum" notnull_strength="0" unique_strength="0" constraints="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="q_out_x_sum" desc="" exp=""/>
    <constraint field="q_out_y_sum" desc="" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column width="-1" name="q_out_x_sum" hidden="0" type="field"/>
      <column width="-1" name="q_out_y_sum" hidden="0" type="field"/>
      <column width="-1" hidden="1" type="actions"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="id" editable="1"/>
    <field name="node_type" editable="1"/>
    <field name="node_type_description" editable="1"/>
    <field name="q_out_x_sum" editable="1"/>
    <field name="q_out_y_sum" editable="1"/>
    <field name="spatialite_id" editable="1"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="id"/>
    <field labelOnTop="0" name="node_type"/>
    <field labelOnTop="0" name="node_type_description"/>
    <field labelOnTop="0" name="q_out_x_sum"/>
    <field labelOnTop="0" name="q_out_y_sum"/>
    <field labelOnTop="0" name="spatialite_id"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
