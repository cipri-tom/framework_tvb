"""
A dummy visualiser for experimenting with WebGL frameworks
"""

import json
import numpy
import tvb.datatypes.time_series as tsdata
from tvb.core.adapters.abcdisplayer import ABCDisplayer
from tvb.core.entities.storage import dao
from tvb.datatypes.surfaces import RegionMapping, FaceSurface
from tvb.datatypes.time_series import TimeSeries, TimeSeriesSurface


class TestVisualiser(ABCDisplayer):

    _ui_name = "TEST"

    def get_input_tree(self):
        """
        Inform caller of the data we need as input.
        """
        return [{"name": "time_series",
                 "type": tsdata.TimeSeries,
                 "required": True
                 }]

    def launch(self, time_series):
        one_to_one_map, url_vertices, url_normals, url_triangles, \
            alphas, alphas_indices, region_map = self._prepare_surface_urls(time_series)

        min_val, max_val = time_series.get_min_max_values()

        params = dict(title="WebGL Framework visualiser", isOneToOneMapping=one_to_one_map,
                    urlVertices=json.dumps(url_vertices), urlTriangles=json.dumps(url_triangles),
                    urlNormals=json.dumps(url_normals),
                    # alphas=json.dumps(alphas), alphas_indices=json.dumps(alphas_indices), # not needed for now
                    timeSeriesGid=time_series.gid, minActivity=min_val, maxActivity=max_val)
        if one_to_one_map:
            params["regionMappingGid"] = region_map.gid
        return self.build_display_result("test/view", params)

    def _prepare_surface_urls(self, time_series):
        """
        Prepares the urls from which the client may read the data needed for drawing the surface.
        """
        one_to_one_map = isinstance(time_series, TimeSeriesSurface)
        if not one_to_one_map:
            region_map = dao.get_generic_entity(RegionMapping, time_series.connectivity.gid, '_connectivity')
            if len(region_map) < 1:
                raise Exception("No Mapping Surface found for display!")
            region_map = region_map[0]
            surface = region_map.surface
        else:
            region_map = None
            surface = time_series.surface

        if surface is None:
            raise Exception("No not-none Mapping Surface found for display!")

        url_vertices, url_normals, url_triangles, alphas, alphas_indices = surface.get_urls_for_rendering(True,
                                                                                                          region_map)
        return one_to_one_map, url_vertices, url_normals, url_triangles, alphas, alphas_indices, region_map