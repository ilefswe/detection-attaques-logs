package securite;

import java.io.IOException;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

/**
 * Combiner : additionne localement les 1 sur chaque machine, SANS filtrer.
 * (Il ne faut pas appliquer le seuil ici : une IP peut avoir 10 échecs sur
 *  un worker et 15 sur l'autre ; c'est seulement le total qui compte.)
 */
public class SommeCombiner extends Reducer<Text, IntWritable, Text, IntWritable> {

    private final IntWritable total = new IntWritable();

    @Override
    protected void reduce(Text cle, Iterable<IntWritable> valeurs, Context context)
            throws IOException, InterruptedException {
        int somme = 0;
        for (IntWritable v : valeurs) {
            somme += v.get();
        }
        total.set(somme);
        context.write(cle, total);
    }
}
