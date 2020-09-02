<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyMaxScale="1" simplifyLocal="1" simplifyDrawingTol="1" simplifyDrawingHints="0" labelsEnabled="0" version="3.14.0-Pi" maxScale="0" readOnly="0" hasScaleBasedVisibilityFlag="0" minScale="100000000" simplifyAlgorithm="0" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal durationField="" accumulate="0" startField="" endExpression="" mode="0" enabled="0" startExpression="" endField="" durationUnit="min" fixedDuration="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <renderer-v2 type="graduatedSymbol" enableorderby="0" forceraster="0" symbollevels="0" attr="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" graduatedMethod="GraduatedColor">
    <ranges>
      <range symbol="0" render="true" lower="0.000000000000000" upper="4.132510710368467" label="0 - 4.1"/>
      <range symbol="1" render="true" lower="4.132510710368467" upper="13.002197735127176" label="4.1 - 13"/>
      <range symbol="2" render="true" lower="13.002197735127176" upper="27.951982401709977" label="13 - 28"/>
      <range symbol="3" render="true" lower="27.951982401709977" upper="53.153704979597173" label="28 - 53.2"/>
      <range symbol="4" render="true" lower="53.153704979597173" upper="96.509018524428484" label="53.2 - 96.5"/>
      <range symbol="5" render="true" lower="96.509018524428484" upper="181.956647328349106" label="96.5 - 182"/>
      <range symbol="6" render="true" lower="181.956647328349106" upper="366.815852146013583" label="182 - 366.8"/>
      <range symbol="7" render="true" lower="366.815852146013583" upper="820.149457974956249" label="366.8 - 820.1"/>
      <range symbol="8" render="true" lower="820.149457974956249" upper="2184.838451207896924" label="820.1 - 2184.8"/>
      <range symbol="9" render="true" lower="2184.838451207896924" upper="99272.573036079265876" label="2184.8 - 99272.6"/>
    </ranges>
    <symbols>
      <symbol type="marker" name="0" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="1" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="226,238,249,255" k="color"/>
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="2" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="205,224,242,255" k="color"/>
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="3" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="4" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="137,191,221,255" k="color"/>
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="5" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="96,166,210,255" k="color"/>
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="6" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="7" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="33,114,182,255" k="color"/>
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="8" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
          <prop v="0" k="angle"/>
          <prop v="10,84,158,255" k="color"/>
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol type="marker" name="9" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <source-symbol>
      <symbol type="marker" name="0" clip_to_extent="1" alpha="1" force_rhr="0">
        <layer pass="0" locked="0" enabled="1" class="SvgMarker">
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
          <prop v="2" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="angle">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="degrees(azimuth( make_point( 0,0), make_point( &quot;q_out_x_sum&quot;,  &quot;q_out_y_sum&quot; )))" name="expression"/>
                  <Option type="int" value="3" name="type"/>
                </Option>
                <Option type="Map" name="size">
                  <Option type="bool" value="true" name="active"/>
                  <Option type="QString" value="sqrt(&quot;q_out_x_sum&quot; * &quot;q_out_x_sum&quot; + &quot;q_out_y_sum&quot; * &quot;q_out_y_sum&quot;)" name="expression"/>
                  <Option type="Map" name="transformer">
                    <Option type="Map" name="d">
                      <Option type="double" value="0.57" name="exponent"/>
                      <Option type="double" value="2" name="maxSize"/>
                      <Option type="double" value="750" name="maxValue"/>
                      <Option type="double" value="0" name="minSize"/>
                      <Option type="double" value="0" name="minValue"/>
                      <Option type="double" value="0" name="nullSize"/>
                      <Option type="int" value="2" name="scaleType"/>
                    </Option>
                    <Option type="int" value="1" name="t"/>
                  </Option>
                  <Option type="int" value="3" name="type"/>
                </Option>
              </Option>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </source-symbol>
    <colorramp type="gradient" name="[source]">
      <prop v="247,251,255,255" k="color1"/>
      <prop v="8,48,107,255" k="color2"/>
      <prop v="0" k="discrete"/>
      <prop v="gradient" k="rampType"/>
      <prop v="0.13;222,235,247,255:0.26;198,219,239,255:0.39;158,202,225,255:0.52;107,174,214,255:0.65;66,146,198,255:0.78;33,113,181,255:0.9;8,81,156,255" k="stops"/>
    </colorramp>
    <classificationMethod id="Quantile">
      <symmetricMode enabled="0" symmetrypoint="0" astride="0"/>
      <labelFormat trimtrailingzeroes="1" format="%1 - %2" labelprecision="1"/>
      <parameters>
        <Option/>
      </parameters>
      <extraInformation/>
    </classificationMethod>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames">
      <value>vfr_metres_to_unit</value>
      <value>vfr_scale</value>
    </property>
    <property key="variableValues">
      <value>1.9349746982808556</value>
      <value>1.0</value>
    </property>
    <property value="" key="vfr_scale_group"/>
    <property value="1" key="vfr_scale_group_factor"/>
    <property value="{&quot;arrowAngleDegrees&quot;: false, &quot;arrowAngleFromNorth&quot;: true, &quot;arrowBorderColor&quot;: &quot;#ff000000&quot;, &quot;arrowBorderWidth&quot;: 0.0, &quot;arrowFillColor&quot;: &quot;#ff000000&quot;, &quot;arrowHeadRelativeLength&quot;: 1.5, &quot;arrowHeadWidth&quot;: 3.0, &quot;arrowMaxRelativeHeadSize&quot;: 0.3, &quot;arrowMode&quot;: &quot;xy&quot;, &quot;arrowShaftWidth&quot;: 0.75, &quot;baseBorderColor&quot;: &quot;#ff000000&quot;, &quot;baseBorderWidth&quot;: 0.0, &quot;baseFillColor&quot;: &quot;#ffff0000&quot;, &quot;baseSize&quot;: 2.0, &quot;drawArrow&quot;: true, &quot;drawEllipse&quot;: true, &quot;drawEllipseAxes&quot;: false, &quot;dxField&quot;: &quot;q_out_x_sum&quot;, &quot;dyField&quot;: &quot;q_out_y_sum&quot;, &quot;ellipseAngleFromNorth&quot;: true, &quot;ellipseBorderColor&quot;: &quot;#ff000000&quot;, &quot;ellipseBorderWidth&quot;: 0.7, &quot;ellipseDegrees&quot;: true, &quot;ellipseFillColor&quot;: &quot;#ff000000&quot;, &quot;ellipseMode&quot;: &quot;axes&quot;, &quot;ellipseScale&quot;: 1.0, &quot;ellipseTickSize&quot;: 2.0, &quot;emaxAzimuthField&quot;: &quot;&quot;, &quot;emaxField&quot;: &quot;&quot;, &quot;eminField&quot;: &quot;&quot;, &quot;fillArrow&quot;: true, &quot;fillBase&quot;: true, &quot;fillEllipse&quot;: false, &quot;scale&quot;: 1.0, &quot;scaleGroup&quot;: &quot;&quot;, &quot;scaleGroupFactor&quot;: 1.0, &quot;scaleIsMetres&quot;: false, &quot;symbolRenderUnit&quot;: &quot;mm&quot;}" key="vfr_settings"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory sizeType="MM" penWidth="0" backgroundAlpha="255" scaleBasedVisibility="0" penColor="#000000" backgroundColor="#ffffff" labelPlacementMethod="XHeight" height="15" opacity="1" spacingUnit="MM" maxScaleDenominator="1e+08" spacing="0" barWidth="5" lineSizeScale="3x:0,0,0,0,0,0" minimumSize="0" sizeScale="3x:0,0,0,0,0,0" showAxis="0" direction="1" diagramOrientation="Up" enabled="0" penAlpha="255" width="15" spacingUnitScale="3x:0,0,0,0,0,0" lineSizeType="MM" minScaleDenominator="0" rotationOffset="270" scaleDependency="Area">
      <fontProperties description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0" style=""/>
      <attribute color="#000000" field="" label=""/>
      <axisSymbol>
        <symbol type="line" name="" clip_to_extent="1" alpha="1" force_rhr="0">
          <layer pass="0" locked="0" enabled="1" class="SimpleLine">
            <prop v="square" k="capstyle"/>
            <prop v="5;2" k="customdash"/>
            <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
            <prop v="MM" k="customdash_unit"/>
            <prop v="0" k="draw_inside_polygon"/>
            <prop v="bevel" k="joinstyle"/>
            <prop v="35,35,35,255" k="line_color"/>
            <prop v="solid" k="line_style"/>
            <prop v="0.26" k="line_width"/>
            <prop v="MM" k="line_width_unit"/>
            <prop v="0" k="offset"/>
            <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
            <prop v="MM" k="offset_unit"/>
            <prop v="0" k="ring_filter"/>
            <prop v="0" k="use_custom_dash"/>
            <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
            <data_defined_properties>
              <Option type="Map">
                <Option type="QString" value="" name="name"/>
                <Option name="properties"/>
                <Option type="QString" value="collection" name="type"/>
              </Option>
            </data_defined_properties>
          </layer>
        </symbol>
      </axisSymbol>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings placement="0" showAll="1" obstacle="0" priority="0" zIndex="0" linePlacementFlags="18" dist="0">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <referencedLayers/>
  <referencingLayers/>
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
    <field name="node_type">
      <editWidget type="Range">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="node_type_description">
      <editWidget type="TextEdit">
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
    <alias index="0" name="" field="id"/>
    <alias index="1" name="" field="spatialite_id"/>
    <alias index="2" name="" field="node_type"/>
    <alias index="3" name="" field="node_type_description"/>
    <alias index="4" name="" field="q_out_x_sum"/>
    <alias index="5" name="" field="q_out_y_sum"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" applyOnUpdate="0" field="id"/>
    <default expression="" applyOnUpdate="0" field="spatialite_id"/>
    <default expression="" applyOnUpdate="0" field="node_type"/>
    <default expression="" applyOnUpdate="0" field="node_type_description"/>
    <default expression="" applyOnUpdate="0" field="q_out_x_sum"/>
    <default expression="" applyOnUpdate="0" field="q_out_y_sum"/>
  </defaults>
  <constraints>
    <constraint constraints="0" notnull_strength="0" exp_strength="0" field="id" unique_strength="0"/>
    <constraint constraints="0" notnull_strength="0" exp_strength="0" field="spatialite_id" unique_strength="0"/>
    <constraint constraints="0" notnull_strength="0" exp_strength="0" field="node_type" unique_strength="0"/>
    <constraint constraints="0" notnull_strength="0" exp_strength="0" field="node_type_description" unique_strength="0"/>
    <constraint constraints="0" notnull_strength="0" exp_strength="0" field="q_out_x_sum" unique_strength="0"/>
    <constraint constraints="0" notnull_strength="0" exp_strength="0" field="q_out_y_sum" unique_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint desc="" field="id" exp=""/>
    <constraint desc="" field="spatialite_id" exp=""/>
    <constraint desc="" field="node_type" exp=""/>
    <constraint desc="" field="node_type_description" exp=""/>
    <constraint desc="" field="q_out_x_sum" exp=""/>
    <constraint desc="" field="q_out_y_sum" exp=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig sortOrder="0" actionWidgetStyle="dropDown" sortExpression="">
    <columns>
      <column type="field" name="q_out_x_sum" hidden="0" width="-1"/>
      <column type="field" name="q_out_y_sum" hidden="0" width="-1"/>
      <column type="actions" hidden="1" width="-1"/>
      <column type="field" name="id" hidden="0" width="-1"/>
      <column type="field" name="spatialite_id" hidden="0" width="-1"/>
      <column type="field" name="node_type" hidden="0" width="-1"/>
      <column type="field" name="node_type_description" hidden="0" width="-1"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
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
    <field name="id" labelOnTop="0"/>
    <field name="node_type" labelOnTop="0"/>
    <field name="node_type_description" labelOnTop="0"/>
    <field name="q_out_x_sum" labelOnTop="0"/>
    <field name="q_out_y_sum" labelOnTop="0"/>
    <field name="spatialite_id" labelOnTop="0"/>
  </labelOnTop>
  <dataDefinedFieldProperties/>
  <widgets/>
  <previewExpression>"id"</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
