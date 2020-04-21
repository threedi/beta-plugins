<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis minScale="1e+08" simplifyDrawingTol="1" version="3.4.12-Madeira" maxScale="0" styleCategories="AllStyleCategories" simplifyMaxScale="1" simplifyDrawingHints="0" hasScaleBasedVisibilityFlag="0" readOnly="0" labelsEnabled="0" simplifyAlgorithm="0" simplifyLocal="1">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" forceraster="0" enableorderby="0" type="graduatedSymbol" graduatedMethod="GraduatedColor" attr=" sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)">
    <ranges>
      <range label="0 - 1" upper="0.912141795114463" render="true" symbol="0" lower="0.000000000000000"/>
      <range label="1 - 2" upper="1.667750853626856" render="true" symbol="1" lower="0.912141795114463"/>
      <range label="2 - 3" upper="2.512422574191731" render="true" symbol="2" lower="1.667750853626856"/>
      <range label="3 - 4" upper="3.580593280706106" render="true" symbol="3" lower="2.512422574191731"/>
      <range label="4 - 4" upper="4.489018236634798" render="true" symbol="4" lower="3.580593280706106"/>
      <range label="4 - 5" upper="5.414106970716412" render="true" symbol="5" lower="4.489018236634798"/>
      <range label="5 - 6" upper="6.443884235430079" render="true" symbol="6" lower="5.414106970716412"/>
      <range label="6 - 8" upper="7.851861679842489" render="true" symbol="7" lower="6.443884235430079"/>
      <range label="8 - 10" upper="10.485174045112020" render="true" symbol="8" lower="7.851861679842489"/>
      <range label="10 - 13" upper="13.107374548562900" render="true" symbol="9" lower="10.485174045112020"/>
      <range label="13 - 17" upper="17.111020728312418" render="true" symbol="10" lower="13.107374548562900"/>
      <range label="17 - 22" upper="21.999935153220513" render="true" symbol="11" lower="17.111020728312418"/>
      <range label="22 - 27" upper="27.201040667549290" render="true" symbol="12" lower="21.999935153220513"/>
      <range label="27 - 34" upper="33.714814869056617" render="true" symbol="13" lower="27.201040667549290"/>
      <range label="34 - 41" upper="41.082099530241692" render="true" symbol="14" lower="33.714814869056617"/>
      <range label="41 - 50" upper="50.476893615603061" render="true" symbol="15" lower="41.082099530241692"/>
      <range label="50 - 67" upper="66.775579920546221" render="true" symbol="16" lower="50.476893615603061"/>
      <range label="67 - 88" upper="87.922555691871622" render="true" symbol="17" lower="66.775579920546221"/>
      <range label="88 - 120" upper="119.670403427181284" render="true" symbol="18" lower="87.922555691871622"/>
      <range label="120 - 159" upper="159.261111208668552" render="true" symbol="19" lower="119.670403427181284"/>
      <range label="159 - 212" upper="212.311202744737955" render="true" symbol="20" lower="159.261111208668552"/>
      <range label="212 - 332" upper="331.501332084175829" render="true" symbol="21" lower="212.311202744737955"/>
      <range label="332 - 553" upper="552.630441723761578" render="true" symbol="22" lower="331.501332084175829"/>
      <range label="553 - 1985" upper="1985.259193546342658" render="true" symbol="23" lower="552.630441723761578"/>
      <range label="1985 - 8832" upper="8831.561189195606858" render="true" symbol="24" lower="1985.259193546342658"/>
    </ranges>
    <symbols>
      <symbol name="0" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="247,251,255,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="1" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="239,246,253,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="10" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="148,197,223,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="11" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="131,188,220,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="12" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="115,179,216,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="13" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="100,169,212,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="14" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="87,160,207,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="15" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="74,151,201,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="16" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="62,142,196,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="17" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="51,131,191,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="18" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="40,121,185,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="19" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="30,110,179,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="2" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="231,241,250,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="20" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="21,99,170,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="21" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="13,88,161,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="22" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="8,75,148,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="23" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="8,61,127,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="24" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="8,48,107,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="3" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="223,236,248,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="4" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="216,231,245,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="5" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="208,226,243,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="6" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="200,221,240,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="7" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="188,215,236,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="8" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="176,210,232,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="9" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="163,204,227,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <symbol name="0" force_rhr="0" clip_to_extent="1" alpha="1" type="marker">
        <layer enabled="1" pass="0" locked="0" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="0,0,0,255" k="color"/>
          <prop v="2" k="fixedAspectRatio"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="arrows/Arrow_05.svg" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="35,35,35,255" k="outline_color"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="3" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
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
      <prop v="247,251,255,255" k="color1"/>
      <prop v="8,48,107,255" k="color2"/>
      <prop v="0" k="discrete"/>
      <prop v="gradient" k="rampType"/>
      <prop v="0.13;222,235,247,255:0.26;198,219,239,255:0.39;158,202,225,255:0.52;107,174,214,255:0.65;66,146,198,255:0.78;33,113,181,255:0.9;8,81,156,255" k="stops"/>
    </colorramp>
    <mode name="quantile"/>
    <symmetricMode enabled="false" astride="false" symmetryPoint="0"/>
    <rotation/>
    <sizescale/>
    <labelformat format="%1 - %2" trimtrailingzeroes="false" decimalplaces="2"/>
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
    <DiagramCategory labelPlacementMethod="XHeight" lineSizeScale="3x:0,0,0,0,0,0" scaleDependency="Area" sizeType="MM" penAlpha="255" diagramOrientation="Up" enabled="0" penWidth="0" scaleBasedVisibility="0" penColor="#000000" backgroundColor="#ffffff" sizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" rotationOffset="270" height="15" width="15" lineSizeType="MM" barWidth="5" maxScaleDenominator="1e+08" minimumSize="0" minScaleDenominator="0" opacity="1">
      <fontProperties description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0" style=""/>
      <attribute label="" field="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="18" dist="0" obstacle="0" placement="0" priority="0" showAll="1" zIndex="0">
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
    <field name="id">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="spatialite_id">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
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
    <alias name="" field="id" index="0"/>
    <alias name="" field="spatialite_id" index="1"/>
    <alias name="" field="q_out_x_sum" index="2"/>
    <alias name="" field="q_out_y_sum" index="3"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="id" expression=""/>
    <default applyOnUpdate="0" field="spatialite_id" expression=""/>
    <default applyOnUpdate="0" field="q_out_x_sum" expression=""/>
    <default applyOnUpdate="0" field="q_out_y_sum" expression=""/>
  </defaults>
  <constraints>
    <constraint unique_strength="0" notnull_strength="0" exp_strength="0" constraints="0" field="id"/>
    <constraint unique_strength="0" notnull_strength="0" exp_strength="0" constraints="0" field="spatialite_id"/>
    <constraint unique_strength="0" notnull_strength="0" exp_strength="0" constraints="0" field="q_out_x_sum"/>
    <constraint unique_strength="0" notnull_strength="0" exp_strength="0" constraints="0" field="q_out_y_sum"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="id" exp=""/>
    <constraint desc="" field="spatialite_id" exp=""/>
    <constraint desc="" field="q_out_x_sum" exp=""/>
    <constraint desc="" field="q_out_y_sum" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" sortExpression="" actionWidgetStyle="dropDown">
    <columns>
      <column name="id" type="field" width="-1" hidden="0"/>
      <column name="spatialite_id" type="field" width="-1" hidden="0"/>
      <column name="q_out_x_sum" type="field" width="-1" hidden="0"/>
      <column name="q_out_y_sum" type="field" width="-1" hidden="0"/>
      <column type="actions" width="-1" hidden="1"/>
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
    <field name="q_out_x_sum" editable="1"/>
    <field name="q_out_y_sum" editable="1"/>
    <field name="spatialite_id" editable="1"/>
  </editable>
  <labelOnTop>
    <field name="id" labelOnTop="0"/>
    <field name="q_out_x_sum" labelOnTop="0"/>
    <field name="q_out_y_sum" labelOnTop="0"/>
    <field name="spatialite_id" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
