package securite;

import java.io.IOException;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

/**
 * Reducer : fait le total final et n'écrit la clé que si total >= seuil.
 * Pour bruteforce et scan, le seuil (20 par défaut) transforme le comptage en ALERTE.
 */
public class AlerteReducer extends Reducer<Text, IntWritable, Text, IntWritable> {

    private final IntWritable total = new IntWritable();
    private int seuil;

    @Override
    protected void setup(Context context) {
        seuil = context.getConfiguration().getInt("seuil", 1);
    }

    @Override
    protected void reduce(Text cle, Iterable<IntWritable> valeurs, Context context)
            throws IOException, InterruptedException {
        int somme = 0;
        for (IntWritable v : valeurs) {
            somme += v.get();
        }
        if (somme >= seuil) {
            total.set(somme);
            context.write(cle, total);
            context.getCounter("Securite", "Alertes").increment(1);
        }
    }
}
