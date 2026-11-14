package securite;

import java.io.IOException;
import java.net.URLDecoder;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

/**
 * Lit une ligne de log Apache (format "combined") :
 * 192.168.1.10 - - [14/Nov/2026:10:15:32 +0100] "GET /index.html HTTP/1.1" 200 5120 "-" "Mozilla/5.0"
 *
 * Selon le mode choisi, émet (clé, 1) :
 *   ip         -> (IP, 1)                        : nombre de requêtes par IP (flood / DoS)
 *   statut     -> (code HTTP, 1)                 : répartition des codes 200, 404, 401...
 *   bruteforce -> (IP, 1) si POST /login -> 401  : échecs de connexion par IP
 *   scan       -> (IP, 1) si réponse 404         : pages inexistantes demandées par IP
 *   attaques   -> (type d'attaque, 1)            : SQL Injection, XSS, Path Traversal
 */
public class LogMapper extends Mapper<LongWritable, Text, Text, IntWritable> {

    // IP, date, méthode, URL, code HTTP
    private static final Pattern LOG = Pattern.compile(
            "^(\\S+) \\S+ \\S+ \\[([^\\]]+)\\] \"(\\S+) (\\S+)[^\"]*\" (\\d{3}) .*");

    private static final IntWritable UN = new IntWritable(1);
    private final Text cle = new Text();
    private String mode;

    @Override
    protected void setup(Context context) {
        mode = context.getConfiguration().get("mode", "ip");
    }

    @Override
    protected void map(LongWritable offset, Text ligne, Context context)
            throws IOException, InterruptedException {
        Matcher m = LOG.matcher(ligne.toString());
        if (!m.matches()) {                                   // ligne illisible -> ignorée
            context.getCounter("Qualite", "LignesInvalides").increment(1);
            return;
        }
        String ip = m.group(1);
        String methode = m.group(3);
        String url = m.group(4);
        String statut = m.group(5);

        switch (mode) {
            case "ip":
                emettre(context, ip);
                break;
            case "statut":
                emettre(context, statut);
                break;
            case "bruteforce":
                if (methode.equals("POST") && url.startsWith("/login") && statut.equals("401")) {
                    emettre(context, ip);
                }
                break;
            case "scan":
                if (statut.equals("404")) {
                    emettre(context, ip);
                }
                break;
            case "attaques":
                String type = detecterAttaque(url);
                if (type != null) {
                    emettre(context, type);
                    context.getCounter("Securite", "RequetesMalveillantes").increment(1);
                }
                break;
            default:
                throw new IllegalArgumentException("Mode inconnu : " + mode);
        }
    }

    private void emettre(Context context, String valeurCle) throws IOException, InterruptedException {
        cle.set(valeurCle);
        context.write(cle, UN);
    }

    /** Recherche des signatures d'attaques connues dans l'URL décodée. */
    static String detecterAttaque(String url) {
        String u;
        try {
            u = URLDecoder.decode(url, "UTF-8").toLowerCase();  // %27 -> '  ,  %3C -> <
        } catch (Exception e) {
            u = url.toLowerCase();
        }
        if (u.contains("union select") || u.contains("' or '1'='1") || u.contains("' or 1=1")
                || u.contains("sleep(") || u.contains("--")) {
            return "SQL Injection";
        }
        if (u.contains("<script") || u.contains("javascript:") || u.contains("onerror=")) {
            return "XSS";
        }
        if (u.contains("../") || u.contains("/etc/passwd")) {
            return "Path Traversal";
        }
        return null;
    }
}
