# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
import settings

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Category'
        db.create_table('treeview_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('position', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('is_draggable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_drop_target', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('cls', self.gf('django.db.models.fields.CharField')(default='keyword', max_length=20)),
        ))
        db.send_create_signal('treeview', ['Category'])

        # Adding model 'Node'
        using_mysql = (settings.DATABASES['default']['ENGINE']
                       == 'django.db.backends.mysql')
        node_fields = [
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['treeview.Node'])),
            ('depth', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('cls', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('rgt', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('creation_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('is_draggable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_drop_target', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('editable', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tree_nodes', to=orm['workspace.DAMWorkspace'])),
            ('associate_ancestors', self.gf('django.db.models.fields.BooleanField')(default=False))
            ]

        # FIXME: ugly kludge for dealing with MySQL quirks
        # We need to force the node.kb_object_id field to use ASCII encoding,
        # in order to be useable as a reference to kb_object.id with InnoDB.
        # However, there appears to be no way to do it using the
        # Django model API.  Thus, we check whether MySQL is in use
        # --- and if it is the case, we will take care of the
        # node.kb_object_id field, emitting some custom SQL after the 'node'
        # table is created.
        if not using_mysql:
            node_fields.append(('kb_object', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='catalog_nodes', null=True, blank=True, to=orm['kb.Object'])))
        db.create_table('node', node_fields)
        if using_mysql:
            db.execute('ALTER TABLE node ADD COLUMN kb_object_id VARCHAR(128) '
                       'CHARACTER SET ascii DEFAULT NULL')
            db.execute('ALTER TABLE node '
                       'ADD CONSTRAINT kb_object_id_refs_id_ff54beb '
                       'FOREIGN KEY (kb_object_id) REFERENCES kb_object(id)')
        db.send_create_signal('treeview', ['Node'])

        # Adding M2M table for field items on 'Node'
        db.create_table('node_items', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('node', models.ForeignKey(orm['treeview.node'], null=False)),
            ('item', models.ForeignKey(orm['repository.item'], null=False))
        ))
        db.create_unique('node_items', ['node_id', 'item_id'])

        # Adding model 'NodeMetadataAssociation'
        db.create_table('treeview_nodemetadataassociation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treeview.Node'])),
            ('metadata_schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['metadata.MetadataProperty'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('treeview', ['NodeMetadataAssociation'])

        # Adding model 'SmartFolderNodeAssociation'
        db.create_table('treeview_smartfoldernodeassociation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('smart_folder', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treeview.SmartFolder'])),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['treeview.Node'])),
            ('negated', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('treeview', ['SmartFolderNodeAssociation'])

        # Adding model 'SmartFolder'
        db.create_table('treeview_smartfolder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('and_condition', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('workspace', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['workspace.DAMWorkspace'])),
        ))
        db.send_create_signal('treeview', ['SmartFolder'])


    def backwards(self, orm):
        
        # Deleting model 'Category'
        db.delete_table('treeview_category')

        # Deleting model 'Node'
        db.delete_table('node')

        # Removing M2M table for field items on 'Node'
        db.delete_table('node_items')

        # Deleting model 'NodeMetadataAssociation'
        db.delete_table('treeview_nodemetadataassociation')

        # Deleting model 'SmartFolderNodeAssociation'
        db.delete_table('treeview_smartfoldernodeassociation')

        # Deleting model 'SmartFolder'
        db.delete_table('treeview_smartfolder')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'dam_metadata.xmpnamespace': {
            'Meta': {'object_name': 'XMPNamespace'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'prefix': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True'}),
            'uri': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'dam_metadata.xmpproperty': {
            'Meta': {'object_name': 'XMPProperty'},
            'caption': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'field_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_array': ('django.db.models.fields.CharField', [], {'default': "'not_array'", 'max_length': '15'}),
            'is_choice': ('django.db.models.fields.CharField', [], {'default': "'not_choice'", 'max_length': '15'}),
            'media_type': ('django.db.models.fields.related.ManyToManyField', [], {'default': "'image'", 'to': "orm['dam_repository.Type']", 'symmetrical': 'False'}),
            'namespace': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dam_metadata.XMPNamespace']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'text'", 'max_length': '128'})
        },
        'dam_repository.type': {
            'Meta': {'object_name': 'Type'},
            'ext': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'subname': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'dam_workspace.workspace': {
            'Meta': {'unique_together': "(('name', 'creator'),)", 'object_name': 'Workspace'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'workspaces'", 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'kb.object': {
            'Meta': {'object_name': 'Object', 'managed': 'False'},
            'id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'metadata.metadataproperty': {
            'Meta': {'object_name': 'MetadataProperty', '_ormbases': ['dam_metadata.XMPProperty']},
            'creation_date': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'file_name_target': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'file_size_target': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_searchable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_variant': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'item_owner_target': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'keyword_target': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'latitude_target': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'longitude_target': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'resource_format': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'rights_target': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'uploaded_by': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'xmpproperty_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['dam_metadata.XMPProperty']", 'unique': 'True', 'primary_key': 'True'})
        },
        'metadata.metadatavalue': {
            'Meta': {'object_name': 'MetadataValue'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['metadata.MetadataProperty']", 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {}),
            'xpath': ('django.db.models.fields.TextField', [], {})
        },
        'repository.item': {
            'Meta': {'object_name': 'Item', 'db_table': "'item'"},
            '_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_column': "'md_id'"}),
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_items'", 'null': 'True', 'to': "orm['auth.User']"}),
            'source_file_path': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['dam_repository.Type']"}),
            'update_time': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'uploader': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'uploaded_items'", 'null': 'True', 'to': "orm['auth.User']"})
        },
        'treeview.category': {
            'Meta': {'object_name': 'Category'},
            'cls': ('django.db.models.fields.CharField', [], {'default': "'keyword'", 'max_length': '20'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_draggable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_drop_target': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'position': ('django.db.models.fields.IntegerField', [], {'unique': 'True'})
        },
        'treeview.node': {
            'Meta': {'object_name': 'Node', 'db_table': "'node'"},
            'associate_ancestors': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cls': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'creation_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'depth': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_draggable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_drop_target': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'items': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['repository.Item']", 'symmetrical': 'False'}),
            'kb_object': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'catalog_nodes'", 'null': 'True', 'blank': 'True', 'to': "orm['kb.Object']"}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'metadata_schema': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['metadata.MetadataProperty']", 'null': 'True', 'through': "orm['treeview.NodeMetadataAssociation']", 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['treeview.Node']"}),
            'rgt': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tree_nodes'", 'to': "orm['workspace.DAMWorkspace']"})
        },
        'treeview.nodemetadataassociation': {
            'Meta': {'object_name': 'NodeMetadataAssociation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata_schema': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['metadata.MetadataProperty']"}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treeview.Node']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'treeview.smartfolder': {
            'Meta': {'object_name': 'SmartFolder'},
            'and_condition': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'nodes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['treeview.Node']", 'through': "orm['treeview.SmartFolderNodeAssociation']", 'symmetrical': 'False'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['workspace.DAMWorkspace']"})
        },
        'treeview.smartfoldernodeassociation': {
            'Meta': {'object_name': 'SmartFolderNodeAssociation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'negated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treeview.Node']"}),
            'smart_folder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['treeview.SmartFolder']"})
        },
        'workspace.damworkspace': {
            'Meta': {'object_name': 'DAMWorkspace', '_ormbases': ['dam_workspace.Workspace']},
            'items': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'workspaces'", 'symmetrical': 'False', 'through': "orm['workspace.WorkspaceItem']", 'to': "orm['repository.Item']"}),
            'workspace_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['dam_workspace.Workspace']", 'unique': 'True', 'primary_key': 'True'})
        },
        'workspace.workspaceitem': {
            'Meta': {'unique_together': "(('item', 'workspace'),)", 'object_name': 'WorkspaceItem'},
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['repository.Item']"}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'workspace': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['workspace.DAMWorkspace']"})
        }
    }

    complete_apps = ['treeview']
