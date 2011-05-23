
from twisted.internet import defer

def run(workspace,            # workspace object
        item_id,              # item pk
        source_variant_name,  # name of the source variant (a string)
        output_variant_name,  # name of the destination variat (a string)
        output_preset,        # CMD_<output_preset> must be one of the gstreamer pipelines below
        **preset_params):     # additional parameters (see pipeline for explanation)

    print
    print '  ****  Script a1:'
    print '  ****  item_id            ',  item_id
    print '  ****  source_variant_name',  source_variant_name
    print '  ****  output_variant_name',  output_variant_name
    print '  ****  output_preset      ',  output_preset
    print '  ****  preset_params      ',  preset_params          
    print '  ****  '
    deferred = defer.Deferred()
    deferred.callback('done')
    return deferred
