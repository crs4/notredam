
from twisted.internet import defer

def run(workspace,            # workspace object
        item_id,              # item pk
        source_variant_name,  # name of the source variant (a string)
        output_variant_name,  # name of the destination variat (a string)
        output_preset,        # CMD_<output_preset> must be one of the gstreamer pipelines below
        **preset_params):     # additional parameters (see pipeline for explanation)

    print
    print '  ****  a1 on %s: source_variant_name' % item_id,  source_variant_name
    print '  ****  a1 on %s: output_variant_name' % item_id,  output_variant_name
    print '  ****  a1 on %s: output_preset      ' % item_id,  output_preset
    print '  ****  a1 on %s: preset_params      ' % item_id,  preset_params          
    print ' '
    deferred = defer.Deferred()
    deferred.callback('done')
    return deferred
