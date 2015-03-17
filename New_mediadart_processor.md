# Introduction #
The state machine implemented by the MachineState/Machine/Action models was activated by the mediadart\_processor that polled the state saved int the DB 1 time per second. This introduces delays and upper limits on the performance of Notredam, which are especially significant when there are many mediadart nodes available.

The optimization introduced here eliminates all polling, and refactors
mediadart\_processor.py as a mediadart server.  This replaces the slow polling of the DB with the fast message passing offered by AMQP, and makes it possible to control the
rate of the requests to mediadart by using the very mechanisms offered by mediadart
itself.

# Details #
The changes made are:
  * deletion of the app **dam.batch\_processor** (which provides the models above)
  * deletion of **mediadart\_processor.py**.
  * addition a new app **dam.mprocessor** which defines a new model "Task" that replaces MachineState/Machine/Action and the helper class **MAction**.
  * addition of a new module **mprocessor.processor.py** which implements a mediadart server that provides the interface to mediadart.  The implementation is a refactoring of the old mediadart\_processor.py.
  * modify **dam.upload.views.py** in order to use the Task/MAction interface.
  * modify **notredam.cfg** in order to start the **dam.mprocessor.processor** server.
  * addition of a new module **start\_mediadart.py** that starts mediadart in such a way that it can have access to the notredam configuration. This is required because the server **dam.mprocessor.processor** needs to have access to the ORM defined by notredam in order to save in the db the results of the media processing (features, metadata, components).


# Results #
Three performance tests have been carried out. The first consisted in uploading 10 pictures (jpg) of 50Kb approx. size.  The second consisted in uploading 15 pictures (jpg) of 700Kb.  A third test consisted in uploading 100 pictures (jpg) of 700Kb approx.
In all tests mprocessor was configured with a degree of parallelism equal to 16, i.e. at
most 16 requests could be running at the same time.

The results are the following:
  * Test1 (10 pictures): mediadart\_processor: 44sec, mprocessor: 9sec.
  * Test2 (15 pictures): mediadart\_processor: 65sec, mprocessor: 16sec.
  * Test3 (100 pictures): mediadart\_processor & mprocessor: fail with uploading error. The development django server could not complete the uploads. The test must be repeated with the Apache production server.

Recall that the processing for each picture requires 8 mediadart operations:
  * 5 feature extractions,(2 for the source, 1 for each of the three variants);
  * 3 adaptions (1 for each variant),
so that the first test requires 80 operations, the second 120 and the third 800.

The time required by mprocessor is slightly less than what is taken by the state machine with continous, 0sec delay polling.