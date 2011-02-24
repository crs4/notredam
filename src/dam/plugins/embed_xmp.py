from dam.core.dam_metadata.models import XMPStructure

def inspect():
    return {
        'name': __name__,
        'parameter_groups':{
        },
        'source_variant': {
            'type': 'input-variant',
            'description': 'input-variant',
            'default': 0,
            'help': ''
        }      
    } 


# Entry point
def run(item_id, workspace, source_variant):
    deferred = defer.Deferred()
    embedder = EmbedXMP(deferred)
    reactor.callLater(0, embedder.execute, item_id, workspace, source_variant)
    return deferred


class EmbedXMP:
    def __init__(self, deferred):
        self.deferred = deferred
        self.workspace = workspace
        self.item = None
        self.component = None

    def _reset_modified_flag(self):
        """
        Reset flags modified in Component and in its metadata
        """
        comp_metadata = self.component.metadata.filter(modified = True)
        for m in comp_metadata:
            m.modified = False
            m.save()
        self.component.modified_metadata = False
        self.component.save()

    def _populate(self, dictionary, metadata, structures):
        for im in metadata:
            if im.schema.namespace.uri not in dictionary:
                dictionary[im.schema.namespace.uri] = {'prefix': im.schema.namespace.prefix, 'fields': {}}
            if im.schema.field_name not in dictionary[im.schema.namespace.uri]['fields']:
                if im.schema.type == 'lang':
                    dictionary[im.schema.namespace.uri]['fields'][im.schema.field_name] = {'type':im.schema.type,'is_array':im.schema.is_array,'value':[im.value],'qualifier':[im.language], 'xpath':[]}
                elif im.schema.type in structures:
                    dictionary[im.schema.namespace.uri]['fields'][im.schema.field_name] = {'type':im.schema.type,'is_array':im.schema.is_array,'value':[im.value],'qualifier':[],'xpath':[im.xpath]}
                else:
                    dictionary[im.schema.namespace.uri]['fields'][im.schema.field_name] = {'type':im.schema.type,'is_array':im.schema.is_array,'value':[im.value],'qualifier':[],'xpath':[]}
            else:
                dictionary[im.schema.namespace.uri]['fields'][im.schema.field_name]['value'].append(im.value)
                if im.schema.type == 'lang':
                    dictionary[im.schema.namespace.uri]['fields'][im.schema.field_name]['qualifier'].append(im.language)
                elif im.schema.type in structures:
                    dictionary[im.schema.namespace.uri]['fields'][im.schema.field_name]['xpath'].append(im.xpath)
        return dictionary

    def _synchronize_metadata(self):
        changes = {}
        structures = [s.name for s in XMPStructure.objects.all()]
        metadata = self.item.metadata.filter(modified = True)
        self._populate(changes, metadata, structures)

        metadata = self.component.metadata.filter(modified = True)
        self._populate(changes, metadata, structures)
        return changes

    def _cb_embed_reset_xmp(self, result):
        if result:
            self._reset_modified_flag()
        self.deferred.callback(result)
        return result

    def _cb_error(self, failure):
        self.deferred.errback(failure)
        return failure

    def execute(self, item_id, workspace, variant_name):
        self.item = Item.objects.get(pk = item_id)
        source_variant = Variant.objects.get(name = variant_name)
        self.component = self.item.get_variant(workspace, source_variant)
        xmp_embedder_proxy = Proxy('XMPEmbedder') 
        metadata_dict = self._synchronize_metadata(variant_name)
        d = xmp_embedder_proxy.metadata_synch(component.ID, metadata_dict)
        d.addCallback(self._cb_embed_reset_xmp)
        d.addErrback(self._cb_error)
        
